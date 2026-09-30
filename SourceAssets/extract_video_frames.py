import bpy,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'Content/Movies/FencingFrames';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
clip=scene.sequence_editor_create().sequences.new_movie('Reference',str(root/'Content/Movies/fencing_duel_clip.mp4'),1,1)
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.fps=24
scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=94
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
scene.frame_start=1;scene.frame_end=249
scene.render.filepath=str(out/'frame_')
bpy.ops.render.render(animation=True)
shutil.copy2(out/'frame_0249.jpg',out/'frame_0250.jpg')
print('FRAME_EXTRACTION_COMPLETE')
