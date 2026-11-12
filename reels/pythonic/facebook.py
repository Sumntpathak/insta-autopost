"""Facebook Page Reel publishing. Page credentials never leave the runner."""
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request

class Facebook:
    def __init__(self):
        self.page=os.environ.get('FB_PAGE_ID','').strip()
        self.token=os.environ.get('FB_PAGE_TOKEN','').strip()
        if not self.page or not self.token:
            raise RuntimeError('Facebook needs FB_PAGE_ID and FB_PAGE_TOKEN in repository Actions secrets')
        if self.token.startswith('IG'):
            raise RuntimeError('An Instagram-only token cannot publish to a Facebook Page')

    def call(self,path,data=None,method='GET'):
        q=urllib.parse.urlencode(data or {})
        url='https://graph.facebook.com/v23.0/'+path+('?' + q if method=='GET' and q else '')
        request=urllib.request.Request(url,data=q.encode() if method=='POST' else None,
                                      headers={'Authorization':'Bearer '+self.token},method=method)
        try:
            with urllib.request.urlopen(request,timeout=90) as response:return json.load(response)
        except urllib.error.HTTPError as error:
            raise RuntimeError('Facebook HTTP '+str(error.code)+' on '+path) from None

    def check(self):
        page=self.call('me',{'fields':'id,name'})
        if str(page.get('id'))!=self.page:
            raise RuntimeError('FB_PAGE_TOKEN does not belong to the configured FB_PAGE_ID')
        return page

    def upload(self,file):
        result=self.call(self.page+'/video_reels',{'upload_phase':'start'},'POST')
        video=str(result['video_id']);url=result['upload_url']
        parsed=urllib.parse.urlparse(url)
        if parsed.scheme!='https' or parsed.hostname!='rupload.facebook.com':
            raise RuntimeError('Unexpected Facebook upload host')
        data=Path(file).read_bytes()
        req=urllib.request.Request(url,data=data,method='POST',headers={
            'Authorization':'OAuth '+self.token,'offset':'0','file_size':str(len(data)),
            'Content-Type':'application/octet-stream'})
        try:
            with urllib.request.urlopen(req,timeout=180) as response:uploaded=json.load(response)
        except urllib.error.HTTPError as error:
            raise RuntimeError('Facebook upload HTTP '+str(error.code)) from None
        if not uploaded.get('success'):raise RuntimeError('Facebook did not confirm upload')
        return video

    def finish(self,video,caption):
        result=self.call(self.page+'/video_reels',{'upload_phase':'finish','video_id':video,
                        'video_state':'PUBLISHED','description':caption},'POST')
        if not result.get('success'):raise RuntimeError('Facebook did not accept publishing')
        for _ in range(60):
            state=self.call(video,{'fields':'status'}).get('status',{})
            phase=state.get('publishing_phase',{})
            if phase.get('publish_status')=='published':return state
            if state.get('video_status')=='error' or phase.get('status')=='error':
                raise RuntimeError('Facebook video processing failed')
            time.sleep(5)
        raise RuntimeError('Facebook publication unconfirmed; do not blindly retry this video')
