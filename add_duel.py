"""Import the supplied two fencers and place synchronized replay on piste 1."""
import unreal as u
import json, shutil
from pathlib import Path

ROOT=Path(u.Paths.project_dir()).resolve()
DATA=json.loads((ROOT/'SourceAssets/Duel/placement_input.json').read_text())
DEST='/Game/GuansClub/Duel'
MAP='/Game/GuansClub/FencingHall'
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
assets=u.AssetToolsHelpers.get_asset_tools()
assert levels.load_level(MAP)
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
u.EditorAssetLibrary.make_directory(DEST)
srcdir=ROOT/'SourceAssets'/'Duel'
srcdir.mkdir(parents=True,exist_ok=True)
for a in list(actors.get_all_level_actors()):
    if 'GuansDuel' in [str(t) for t in a.tags]: actors.destroy_actor(a)

seqpath=DEST+'/LS_Piste01_Duel'
seq=u.load_asset(seqpath) if u.EditorAssetLibrary.does_asset_exist(seqpath) else assets.create_asset('LS_Piste01_Duel',DEST,u.LevelSequence,u.LevelSequenceFactoryNew())
for b in seq.get_bindings(): b.remove()
seq.set_display_rate(u.FrameRate(24,1))
seq.set_playback_start(0)
seq.set_playback_end(250)
xoffset=-50*(min(d['min'][0] for d in DATA)+max(d['max'][0] for d in DATA))
report={'piste':1,'sequence':seqpath,'fps':24,'duration_seconds':250/24,'x_offset_cm':xoffset,'notes':['No sword geometry is present in supplied FBX files.','Each source has a fixed lateral correction; longitudinal animation is unchanged.','Source reconstructions may contain drift or pose inaccuracies; not corrected here.'],'fencers':[]}
for info in DATA:
    idx=info['id']
    copied=srcdir/f'Fencer_{idx}.fbx'
    source=ROOT/Path(info['source'])
    if source.exists() and source.resolve()!=copied.resolve(): shutil.copy2(source,copied)
    assert copied.exists(), f'Missing source FBX: {copied}'
    opts=u.FbxImportUI()
    for k,v in {'import_mesh':True,'import_as_skeletal':True,'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_SKELETAL_MESH,'import_animations':True,'import_materials':True,'import_textures':True,'create_physics_asset':False}.items(): opts.set_editor_property(k,v)
    for k,v in {'convert_scene':True,'convert_scene_unit':True,'use_t0_as_ref_pose':False,'update_skeleton_reference_pose':False}.items(): opts.skeletal_mesh_import_data.set_editor_property(k,v)
    for k,v in {'use_default_sample_rate':False,'custom_sample_rate':24,'snap_to_closest_frame_boundary':True,'import_bone_tracks':True}.items(): opts.anim_sequence_import_data.set_editor_property(k,v)
    task=u.AssetImportTask()
    for k,v in {'filename':str(copied),'destination_path':DEST+'/Fencer'+idx,'destination_name':'SK_Fencer'+idx,'automated':True,'replace_existing':True,'save':True,'options':opts,'factory':u.FbxFactory()}.items(): task.set_editor_property(k,v)
    assets.import_asset_tasks([task])
    imported=[u.load_asset(p) for p in u.EditorAssetLibrary.list_assets(DEST+'/Fencer'+idx,recursive=True,include_folder=False)]
    sk=next(a for a in imported if isinstance(a,u.SkeletalMesh))
    anim=next(a for a in imported if isinstance(a,u.AnimSequence))
    anim.set_editor_property('enable_root_motion',False)
    anim.set_editor_property('force_root_lock',False)
    duration=anim.get_play_length()
    assert 10<duration<11, f'Unexpected duration {duration}'
    # Neutral, clearly visible material; the source has a single untextured body material.
    matpath=DEST+'/M_ReplayBody_'+idx
    mat=u.load_asset(matpath) if u.EditorAssetLibrary.does_asset_exist(matpath) else assets.create_asset('M_ReplayBody_'+idx,DEST,u.Material,u.MaterialFactoryNew())
    u.MaterialEditingLibrary.delete_all_material_expressions(mat)
    c=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionConstant3Vector)
    color=(.62,.73,.80) if idx=='001' else (.78,.70,.58)
    c.set_editor_property('constant',u.LinearColor(*color,1))
    u.MaterialEditingLibrary.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
    r=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionConstant)
    r.set_editor_property('r',.65)
    u.MaterialEditingLibrary.connect_material_property(r,'',u.MaterialProperty.MP_ROUGHNESS)
    u.MaterialEditingLibrary.recompile_material(mat)
    # Blender Y flips to UE Y; align each source's median centreline to piste 1.
    yoffset=310+100*info['median_y_m']
    zoffset=7.5
    a=actors.spawn_actor_from_class(u.SkeletalMeshActor,u.Vector(xoffset,yoffset,zoffset))
    a.set_actor_label('Piste 1 - Fencer '+idx)
    a.set_editor_property('tags',['GuansDuel','Fencer'+idx])
    comp=a.skeletal_mesh_component
    comp.set_skeletal_mesh_asset(sk)
    comp.set_material(0,mat)
    comp.set_collision_profile_name('NoCollision')
    comp.set_editor_property('visibility_based_anim_tick_option',u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
    comp.set_editor_property('bounds_scale',4.0)
    # Serialized preview pose; the Level Sequence owns both clocks during gameplay.
    comp.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
    preview=comp.get_editor_property('animation_data')
    preview.set_editor_property('anim_to_play',anim)
    preview.set_editor_property('saved_looping',False)
    preview.set_editor_property('saved_playing',False)
    preview.set_editor_property('saved_position',0.0)
    comp.set_editor_property('animation_data',preview)
    binding=seq.add_possessable(a)
    binding.set_name('Fencer '+idx)
    track=binding.add_track(u.MovieSceneSkeletalAnimationTrack)
    section=track.add_section()
    section.set_range(0,250)
    params=section.get_editor_property('params')
    params.set_editor_property('animation',anim)
    params.set_editor_property('force_custom_mode',True)
    section.set_editor_property('params',params)
    report['fencers'].append({'id':idx,'source':info['source'],'mesh':sk.get_path_name(),'animation':anim.get_path_name(),'duration_seconds':duration,'actor_location_cm':[xoffset,yoffset,zoffset],'source_median_y_m':info['median_y_m']})

replay=actors.spawn_actor_from_class(u.LevelSequenceActor,u.Vector(0,310,6))
replay.set_actor_label('Piste 1 - Synchronized Duel Replay')
replay.set_editor_property('tags',['GuansDuel'])
replay.set_sequence(seq)
settings=replay.get_editor_property('playback_settings')
settings.set_editor_property('auto_play',True)
settings.set_editor_property('loop_count',u.MovieSceneSequenceLoopCount(-1))
settings.set_editor_property('disable_camera_cuts',True)
replay.set_editor_property('playback_settings',settings)
u.EditorAssetLibrary.save_directory(DEST,only_if_is_dirty=False,recursive=True)
assert levels.save_current_level()
(ROOT/'duel_setup.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
u.log('DUEL_SETUP_COMPLETE '+json.dumps(report))
