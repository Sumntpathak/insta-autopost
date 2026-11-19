"""Generate a news background through the OpenAI Images API.

The workflow supplies OPENAI_API_KEY. Text overlays are added later by render.py so
the model is asked for a clean editorial background with no text, logos, or watermark.
"""
import argparse,base64,json,os
from pathlib import Path
from openai import OpenAI

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--brief",required=True); ap.add_argument("--output",required=True); a=ap.parse_args()
    brief=json.loads(Path(a.brief).read_text())
    prompt=(
      "Create a clean documentary editorial background image for a global technology news post. "
      "No words, letters, numbers, logos, watermarks, UI panels, or fake newspaper text. "
      "Use a realistic or cinematic visual metaphor for this verified story, with the lower third "
      "and left side kept visually calm for later typography. Balanced composition, natural lighting, "
      "credible newsroom visual language, not sensational, not a portrait of a real person unless "
      "the brief explicitly requires it. Story headline: "+brief["headline"]+". Context: "+brief.get("deck","")
    )
    client=OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    result=client.images.generate(model=os.environ.get("SHIPSTACK_IMAGE_MODEL","gpt-image-2.5-flare"),prompt=prompt,size="1024x1024",quality="medium",n=1)
    data=result.data[0].b64_json
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_bytes(base64.b64decode(data))
    print(a.output)
if __name__=="__main__": main()
