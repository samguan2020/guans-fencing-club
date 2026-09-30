"""Add timeline-controlled reference video and right-hand sabre props."""
import unreal as u,json,shutil
from pathlib import Path
ROOT=Path(u.Paths.project_dir()).resolve()
DEST='/Game/GuansClub/ReplayDisplay'
assets=u.AssetToolsHelpers.get_asset_tools()
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert levels.load_level('/Game/GuansClub/FencingHall')
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
u.EditorAssetLibrary.make_directory(DEST)
for a in list(actors.get_all_level_actors()):
    if 'GuansReplayProps' in [str(t) for t in a.tags]:actors.destroy_actor(a)

def asset(name,cls,factory):
    p=DEST+'/'+name
    return u.load_asset(p) if u.EditorAssetLibrary.does_asset_exist(p) else assets.create_asset(name,DEST,cls,factory)
def import_mesh(filename,name):
    opts=u.FbxImportUI()
    for k,v in {'import_mesh':True,'import_as_skeletal':False,'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH,'import_materials':True,'import_textures':False}.items():opts.set_editor_property(k,v)
    for k,v in {'combine_meshes':True,'auto_generate_collision':False,'convert_scene':True,'convert_scene_unit':True,'transform_vertex_to_absolute':True,'generate_lightmap_u_vs':False}.items():opts.static_mesh_import_data.set_editor_property(k,v)
    task=u.AssetImportTask()
    for k,v in {'filename':str(ROOT/'SourceAssets'/filename),'destination_path':DEST,'destination_name':name,'automated':True,'replace_existing':True,'save':True,'options':opts,'factory':u.FbxFactory()}.items():task.set_editor_property(k,v)
    assets.import_asset_tasks([task])
    return next(u.load_asset(p) for p in task.imported_object_paths if isinstance(u.load_asset(p),u.StaticMesh))
def material(name,color,metal=0,rough=.5):
    m=asset(name,u.Material,u.MaterialFactoryNew())
    u.MaterialEditingLibrary.delete_all_material_expressions(m)
    c=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant3Vector)
    c.set_editor_property('constant',u.LinearColor(*color,1))
    u.MaterialEditingLibrary.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
    for prop,val in [(u.MaterialProperty.MP_METALLIC,metal),(u.MaterialProperty.MP_ROUGHNESS,rough)]:
        e=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant);e.set_editor_property('r',val);u.MaterialEditingLibrary.connect_material_property(e,'',prop)
    u.MaterialEditingLibrary.recompile_material(m)
    return m
def mesh_actor(name,mesh,loc,scale=(1,1,1),mat=None):
    a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*loc))
    a.set_actor_label(name);a.set_editor_property('tags',['GuansReplayProps'])
    a.static_mesh_component.set_static_mesh(mesh)
    a.static_mesh_component.set_collision_profile_name('NoCollision')
    a.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE)
    a.set_actor_scale3d(u.Vector(*scale))
    if mat:a.static_mesh_component.set_material(0,mat)
    return a

sabre=import_mesh('sabre.fbx','SM_Sabre')
steel=material('M_SabreSteel',(.50,.57,.63),.8,.28)
grip=material('M_SabreGrip',(.025,.03,.038),0,.75)
for i,s in enumerate(sabre.static_materials):sabre.set_material(i,grip if 'Grip' in str(s.material_slot_name) else steel)
hands=[]
for fencer in actors.get_all_level_actors():
    if not isinstance(fencer,u.SkeletalMeshActor) or 'GuansDuel' not in [str(t) for t in fencer.tags]:continue
    sword=mesh_actor(fencer.get_actor_label()+' - Sabre',sabre,(0,0,0))
    sword.attach_to_component(fencer.skeletal_mesh_component,'r_hand_JNT',u.AttachmentRule.KEEP_RELATIVE,u.AttachmentRule.KEEP_RELATIVE,u.AttachmentRule.KEEP_RELATIVE,False)
    sword.set_actor_relative_location(u.Vector(-7,2,0),False,False)
    sword.set_actor_relative_rotation(u.Rotator(pitch=0,yaw=180,roll=0),False,False)
    hands.append({'fencer':fencer.get_actor_label(),'socket':'r_hand_JNT','grip_offset_cm':[-7,2,0],'rotation_degrees':{'yaw':180,'pitch':0,'roll':0}})
assert len(hands)==2

movies=ROOT/'Content'/'Movies';movies.mkdir(exist_ok=True)
video=movies/'fencing_duel_clip.mp4'
assert video.is_file(), 'Missing project video: '+str(video)
source=asset('MS_FencingFrames',u.ImgMediaSource,u.ImgMediaSourceFactoryNew())
source.set_sequence_path(str(movies/'FencingFrames'))
source.set_editor_property('frame_rate_override',u.FrameRate(24,1))
player=asset('MP_FencingReference',u.MediaPlayer,u.MediaPlayerFactoryNew())
player.set_editor_property('play_on_open',False)
player.set_looping(False)
texture=asset('MT_FencingReference',u.MediaTexture,u.MediaTextureFactoryNew())
texture.set_editor_property('new_style_output',True)
texture.set_editor_property('auto_clear',False)
texture.set_media_player(player)
texture.update_resource()
screenmat=asset('M_FencingTV',u.Material,u.MaterialFactoryNew())
screenmat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
screenmat.set_editor_property('two_sided',True)
u.MaterialEditingLibrary.delete_all_material_expressions(screenmat)
tex=u.MaterialEditingLibrary.create_material_expression(screenmat,u.MaterialExpressionTextureSample)
tex.set_editor_property('texture',texture)
tex.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_COLOR)
eye=u.MaterialEditingLibrary.create_material_expression(screenmat,u.MaterialExpressionEyeAdaptation)
divide=u.MaterialEditingLibrary.create_material_expression(screenmat,u.MaterialExpressionDivide)
u.MaterialEditingLibrary.connect_material_expressions(tex,'RGB',divide,'A')
u.MaterialEditingLibrary.connect_material_expressions(eye,'',divide,'B')
u.MaterialEditingLibrary.connect_material_property(divide,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
u.MaterialEditingLibrary.recompile_material(screenmat)

tvmesh=import_mesh('tv_screen.fbx','SM_TVScreen')
cube=u.load_asset('/Engine/BasicShapes/Cube.Cube')
frame=material('M_TVFrame',(.013,.018,.025),.3,.38)
mesh_actor('Piste 1 - Wall TV housing',cube,(0,869,350),(6.64,.12,3.84),frame)
mesh_actor('Piste 1 - Synchronized video screen',tvmesh,(0,861,350),mat=screenmat)

seq=u.load_asset('/Game/GuansClub/Duel/LS_Piste01_Duel')
for tr in list(seq.get_tracks()):
    if isinstance(tr,u.MovieSceneMediaTrack):seq.remove_track(tr)
track=seq.add_track(u.MovieSceneMediaTrack)
track.set_display_name('Reference video - synchronized with both fencers')
section=track.add_section();section.set_range(0,250)
for k,v in {'media_source':source,'media_texture':texture,'use_external_media_player':False,'external_media_player':player,'looping':True,'manual_frame_rate_alignment':True,'frame_rate_alignment':u.FrameRate(24,1)}.items():section.set_editor_property(k,v)
section.set_pre_roll_frames(24)
u.EditorAssetLibrary.save_directory(DEST,only_if_is_dirty=False,recursive=True)
u.EditorAssetLibrary.save_loaded_asset(seq)
for suffix in ['001','002']:
    mat=u.load_asset('/Game/GuansClub/Duel/M_ReplayBody_'+suffix)
    u.MaterialEditingLibrary.set_material_usage(mat,u.MaterialUsage.MATUSAGE_SKELETAL_MESH)
    u.EditorAssetLibrary.save_loaded_asset(mat)
assert levels.save_current_level()
report={'screen':{'wall':'north wall behind piste 1','size_cm':[640,360],'centre_cm':[0,861,350],'source':source.get_path_name(),'player':'Sequencer-managed runtime MediaPlayer','texture':texture.get_path_name()},'swords':hands,'sync':{'sequence':seq.get_path_name(),'fps':24,'range_frames':[0,250],'video_frames':249,'video_seconds':10.375,'note':'1280x720 image sequence derived from MP4, padded with one repeated final frame to the shared 250-frame loop. Internal Sequencer media player drives texture. Audio is not enabled.'},'approximation':'Sabre geometry inferred from reference footage, attached to reconstructed right-hand pose. Not a recovered blade-tip trajectory; no blade bending or fencing hit simulation.'}
(ROOT/'tv_sabres_setup.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
u.log('TV_SABRES_SETUP_COMPLETE '+json.dumps(report))
