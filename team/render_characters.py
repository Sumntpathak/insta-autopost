"""Run with: blender -b -t 4 --python scripts/render_characters.py

Original modeled characters, studio lighting and transparent sprite renders.
Blender is needed only to regenerate assets, not for each reel render.
"""
import bpy
import math
from pathlib import Path
from mathutils import Vector

OUT = Path(__file__).resolve().parent / 'assets/sprites'
OUT.mkdir(parents=True, exist_ok=True)


def material(name, color, rough=.22, coat=.45, metallic=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough
    p.inputs['Metallic'].default_value=metallic
    p.inputs['Coat Weight'].default_value=coat
    p.inputs['Coat Roughness'].default_value=.12
    return m


def sphere(name,loc,scale,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=40,location=loc)
    obj=bpy.context.object; obj.name=name; obj.scale=scale
    obj.data.materials.append(mat)
    for p in obj.data.polygons:p.use_smooth=True
    return obj


def curve(name,points,radius,mat):
    data=bpy.data.curves.new(name,'CURVE'); data.dimensions='3D'; data.bevel_depth=radius; data.bevel_resolution=4
    s=data.splines.new('POLY'); s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    obj=bpy.data.objects.new(name,data); bpy.context.collection.objects.link(obj); obj.data.materials.append(mat)


def setup():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=96
    sc.cycles.use_denoising=False; sc.render.film_transparent=True
    sc.render.resolution_x=384; sc.render.resolution_y=384; sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGBA'
    sc.world.color=(.26,.26,.26)
    sc.view_settings.view_transform='AgX'
    bpy.ops.object.camera_add(location=(0,-7,.45))
    camera=bpy.context.object; camera.rotation_euler=(Vector((0,0,0))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO'; camera.data.ortho_scale=2.65; sc.camera=camera
    for pos,power,size,color in [((-3,-4,5),550,4,(1,.95,.88)),((4,-2,2),400,3,(.8,.9,1)),((1,3,4),650,3,(1,.95,1)),((0,-4,-2),110,4,(.86,.94,1))]:
        bpy.ops.object.light_add(type='AREA',location=pos)
        light=bpy.context.object; light.data.energy=power; light.data.shape='DISK'; light.data.size=size; light.data.color=color
        light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    return sc


def character(name,color,emotion):
    sc=setup()
    body=material('Candy glaze',color,.19,.65)
    body.node_tree.nodes.get('Principled BSDF').inputs['Subsurface Weight'].default_value=.035
    white=material('Porcelain eyes',(.96,.98,1),.18)
    black=material('Ink',(.009,.016,.045),.26)
    iris=material('Iris',(.025,.055,.13),.2)
    pink=material('Smile',(.95,.12,.24),.3)
    sphere('Marble',(0,0,0),(1,1,1),body)
    for side in (-1,1):
        x=side*.34
        if emotion=='blink':
            curve('Closed eyelid',[(x+(i/12-.5)*.3,-.982,-.015+.07*math.sin(i/12*math.pi)) for i in range(13)],.026,black)
        else:
            sphere('Eye',(x,-.9,.05),(.205,.135,.265),white)
            sphere('Iris',(x+.025,-1.027,.035),(.123,.052,.171),iris)
            sphere('Pupil',(x+.03,-1.068,.03),(.073,.025,.113),black)
            sphere('Catchlight',(x-.008,-1.089,.102),(.043,.015,.052),white)
        height=.43 if emotion=='surprised' else .38
        curve('Eyebrow',[(x+(i/12-.5)*.29,-.91,height+.035*math.sin(i/12*math.pi)+(i/12-.5)*(.14 if emotion=='curious' and side==-1 else 0)) for i in range(13)],.025,black)
    if emotion=='surprised':
        sphere('O mouth',(0,-.92,-.4),(.13,.07,.18),black)
    elif emotion=='curious':
        curve('Small smile',[(.08+(i/16-.5)*.23,-.947,-.32-.06*math.sin(i/16*math.pi)) for i in range(17)],.025,black)
    else:
        sphere('Open smile',(0,-.93,-.34),(.25,.065,.17),black)
        sphere('Tongue',(.03,-.991,-.41),(.12,.018,.05),pink)
    sc.render.filepath=str(OUT/f'{name}-{emotion}.png'); bpy.ops.render.render(write_still=True)


for name,color in [('sunny',(1,.52,.025)),('blu',(.025,.3,.95))]:
    for emotion in ('curious','surprised','happy','blink'):
        character(name,color,emotion)

# A rounded, hollow modeled cup with a glazed surface and a rolled rim.
sc=setup(); sc.camera.data.ortho_scale=3.05
pink=material('Rose glaze',(.86,.055,.24),.2,.7)
rim=material('Milky rim',(.96,.82,.86),.22,.5)
profile=[(0,.95),(.63,.95),(.69,.91),(.94,-.81),(.96,-.9),(.92,-.95),(.85,-.95),(.83,-.88),(.60,.78),(0,.78)]
verts=[]; faces=[]; segments=96
for radius,z in profile:
    for i in range(segments):
        angle=i/segments*2*math.pi
        verts.append((radius*math.cos(angle),radius*math.sin(angle),z))
for j in range(len(profile)-1):
    for i in range(segments):
        a=j*segments+i; b=j*segments+(i+1)%segments
        faces.append((a,b,b+segments,a+segments))
mesh=bpy.data.meshes.new('Lathed cup'); mesh.from_pydata(verts,[],faces); mesh.update()
obj=bpy.data.objects.new('Cup',mesh); bpy.context.collection.objects.link(obj); obj.data.materials.append(pink)
for p in mesh.polygons:p.use_smooth=True
bevel=obj.modifiers.new('Rounded lip','BEVEL'); bevel.width=.025; bevel.segments=3
for z,rad in [(-.65,.90),(-.53,.88)]:
    bpy.ops.mesh.primitive_torus_add(major_radius=rad,minor_radius=.025,major_segments=96,minor_segments=12,location=(0,0,z))
    bpy.context.object.data.materials.append(rim)
sc.render.filepath=str(OUT/'cup.png'); bpy.ops.render.render(write_still=True)
