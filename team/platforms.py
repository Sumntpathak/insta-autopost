"""Official Meta adapters. Credentials remain in Actions secrets, never journals."""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request


class APIError(RuntimeError):
    def __init__(self,status,code=None,subcode=None):
        self.status=status; self.code=code; self.subcode=subcode
        super().__init__(f'Meta HTTP {status}; code={code}; subcode={subcode}')


class Graph:
    def __init__(self,token,host='graph.facebook.com'):
        if not token: raise RuntimeError('Required Meta credential is absent')
        self.token=token; self.host=host
        self.version=os.environ.get('META_API_VERSION','v23.0')

    def call(self,path,data=None,method='GET'):
        if '://' in path or '..' in path: raise ValueError('Graph paths must be relative')
        query=urllib.parse.urlencode(data or {})
        url=f'https://{self.host}/{self.version}/{path.lstrip("/")}'
        if method=='GET' and query: url+='?'+query
        req=urllib.request.Request(url,data=query.encode() if method=='POST' else None,method=method,
                                   headers={'Authorization':'Bearer '+self.token})
        try:
            with urllib.request.urlopen(req,timeout=60) as response: return json.load(response)
        except urllib.error.HTTPError as exc:
            try: details=json.load(exc).get('error',{})
            except (ValueError,OSError): details={}
            # Upstream messages and URLs can contain user data or credentials.
            raise APIError(exc.code,details.get('code'),details.get('error_subcode')) from None

    def pages(self,path,params=None,max_pages=None):
        params=dict(params or {}); seen=set(); page=0
        while True:
            response=self.call(path,params)
            yield from response.get('data',[])
            page+=1
            paging=response.get('paging',{})
            if not paging.get('next'): break
            cursor=paging.get('cursors',{}).get('after')
            if not cursor or cursor in seen: raise RuntimeError('Unusable pagination cursor; coverage incomplete')
            seen.add(cursor)
            if max_pages is not None and page>=max_pages: raise RuntimeError('Pagination budget reached; coverage incomplete')
            params['after']=cursor


class Instagram(Graph):
    def __init__(self):
        token=os.environ.get('META_TOKEN','').strip()
        super().__init__(token,'graph.instagram.com' if token.startswith('IG') else 'graph.facebook.com')
        self.id=os.environ.get('IG_USER_ID','').strip()
        if not self.id: raise RuntimeError('IG_USER_ID is absent')

    def check(self,expected):
        account=self.call(self.id,{'fields':'id,username'})
        if account.get('username','').casefold()!=expected.casefold(): raise RuntimeError('Instagram account mismatch')
        return account

    def quota(self):
        value=self.call(self.id+'/content_publishing_limit',{'fields':'quota_usage,config'}).get('data',[])
        if not value or 'quota_usage' not in value[0]: raise RuntimeError('Instagram quota unavailable')
        item=value[0]; config=item.get('config',{})
        total=config.get('quota_total')
        if not isinstance(total,int): raise RuntimeError('Instagram quota capacity unverified')
        return max(0,total-int(item['quota_usage']))

    def ready(self,container):
        # Reels routinely need 1-3 minutes of processing; allow 5 like campaign.Meta.ready.
        for _ in range(100):
            result=self.call(container,{'fields':'status_code'})
            status=result.get('status_code')
            if status=='FINISHED': return
            if status in ('ERROR','EXPIRED'): raise RuntimeError('Instagram container failed processing')
            time.sleep(3)
        raise RuntimeError('Instagram processing timed out')

    def prepare(self,urls,caption,kind):
        if self.quota()<1: raise RuntimeError('Instagram rolling quota exhausted')
        if kind=='reel':
            container=self.call(self.id+'/media',{'media_type':'REELS','video_url':urls[0],'caption':caption,'share_to_feed':'true'},'POST')['id']
        elif len(urls)==1:
            container=self.call(self.id+'/media',{'image_url':urls[0],'caption':caption},'POST')['id']
        else:
            children=[]
            for url in urls:
                child=self.call(self.id+'/media',{'image_url':url,'is_carousel_item':'true'},'POST')['id']
                self.ready(child); children.append(child)
            container=self.call(self.id+'/media',{'media_type':'CAROUSEL','children':','.join(children),'caption':caption},'POST')['id']
        self.ready(container); return str(container)

    def publish(self,container,caption):
        return str(self.call(self.id+'/media_publish',{'creation_id':container},'POST')['id'])

    def comment(self,comment_id,text):
        return self.call(comment_id+'/replies',{'message':text},'POST')['id']


class Facebook(Graph):
    def __init__(self):
        super().__init__(os.environ.get('FB_PAGE_TOKEN','').strip())
        self.id=os.environ.get('FB_PAGE_ID','').strip()
        if not self.id: raise RuntimeError('FB_PAGE_ID is absent')

    def check(self,expected):
        page=self.call('me',{'fields':'id,name'})
        if str(page.get('id'))!=self.id or page.get('name','').casefold()!=expected.casefold():
            raise RuntimeError('Facebook Page token or name mismatch')
        return page

    def prepare(self,urls,caption,kind):
        if kind=='reel':
            response=self.call(self.id+'/video_reels',{'upload_phase':'start'},'POST')
            video=str(response['video_id']); upload=response['upload_url']
            if urllib.parse.urlparse(upload).hostname!='rupload.facebook.com' or not upload.startswith('https://'):
                raise RuntimeError('Unexpected Facebook upload host')
            req=urllib.request.Request(upload,data=b'',method='POST',headers={'Authorization':'OAuth '+self.token,'file_url':urls[0]})
            try:
                with urllib.request.urlopen(req,timeout=120) as r:
                    if not json.load(r).get('success'): raise RuntimeError('Facebook upload not confirmed')
            except urllib.error.HTTPError as e: raise APIError(e.code) from None
            return video
        # Upload unpublished photos. The final feed publication happens separately.
        return [str(self.call(self.id+'/photos',{'url':url,'published':'false'},'POST')['id']) for url in urls]

    def publish(self,container,caption):
        if isinstance(container,str):
            response=self.call(self.id+'/video_reels',{'upload_phase':'finish','video_id':container,'video_state':'PUBLISHED','description':caption},'POST')
            if not response.get('success'): raise RuntimeError('Facebook finish unconfirmed')
            for _ in range(30):
                status=self.call(container,{'fields':'status'}).get('status',{})
                if status.get('publishing_phase',{}).get('publish_status')=='published': return container
                if status.get('video_status')=='error': raise RuntimeError('Facebook video processing failed')
                time.sleep(3)
            raise RuntimeError('Facebook publish result uncertain')
        data={'message':caption}
        data.update({f'attached_media[{i}]':json.dumps({'media_fbid':media}) for i,media in enumerate(container)})
        return str(self.call(self.id+'/feed',data,'POST')['id'])

    def comment(self,comment_id,text):
        return self.call(comment_id+'/comments',{'message':text},'POST')['id']
