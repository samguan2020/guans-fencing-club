"""One-second fading sword-tip history, synchronized to the fixed replay."""
import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir()).resolve();DEST='/Game/GuansClub/TipTrails'
assets=u.AssetToolsHelpers.get_asset_tools();actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
levels.load_level('/Game/GuansClub/FencingHall')
u.EditorAssetLibrary.make_directory(DEST)
for a in list(actors.get_all_level_actors()):
    if 'GuansTipTrail' in map(str,a.tags):actors.destroy_actor(a)
def asset(name,cls,factory):
    p=DEST+'/'+name
    return u.load_asset(p) if u.EditorAssetLibrary.does_asset_exist(p) else assets.create_asset(name,DEST,cls,factory)
mpc=asset('MPC_ReplayClock',u.MaterialParameterCollection,u.MaterialParameterCollectionFactoryNew())
param=u.CollectionScalarParameter();param.set_editor_property('parameter_name','ReplaySeconds');param.set_editor_property('default_value',-1)
mpc.set_editor_property('scalar_parameters',[param])
u.EditorAssetLibrary.save_loaded_asset(mpc)
def mat(name,color,trail):
    m=asset(name,u.Material,u.MaterialFactoryNew());u.MaterialEditingLibrary.delete_all_material_expressions(m)
    m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property('two_sided',True)
    if trail:m.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT)
    def node(cls):return u.MaterialEditingLibrary.create_material_expression(m,cls)
    def connect(a,out,b,inp):u.MaterialEditingLibrary.connect_material_expressions(a,out,b,inp)
    c=node(u.MaterialExpressionConstant3Vector);c.set_editor_property('constant',u.LinearColor(*color,1))
    eye=node(u.MaterialExpressionEyeAdaptation);div=node(u.MaterialExpressionDivide);connect(c,'',div,'A');connect(eye,'',div,'B')
    u.MaterialEditingLibrary.connect_material_property(div,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    if trail:
        clock=node(u.MaterialExpressionCollectionParameter);clock.set_editor_property('collection',mpc);clock.set_editor_property('parameter_name','ReplaySeconds')
        uv=node(u.MaterialExpressionTextureCoordinate)
        custom=node(u.MaterialExpressionCustom);custom.set_editor_property('code','float age = Clock - UV.x; return (age >= 0 && age < 1) ? 0.85 * (1 - age) : 0;')
        custom.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT1)
        inputs=[]
        for name in ['Clock','UV']:
            inp=u.CustomInput();inp.set_editor_property('input_name',name);inputs.append(inp)
        custom.set_editor_property('inputs',inputs);connect(clock,'',custom,'Clock');connect(uv,'',custom,'UV')
        u.MaterialEditingLibrary.connect_material_property(custom,'',u.MaterialProperty.MP_OPACITY)
    u.MaterialEditingLibrary.recompile_material(m)
    return m
def actor(name,mesh,material,scale=(1,1,1)):
    a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0));a.set_actor_label(name);a.tags=['GuansTipTrail']
    a.static_mesh_component.set_static_mesh(mesh);a.static_mesh_component.set_material(0,material);a.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE)
    a.static_mesh_component.set_collision_profile_name('NoCollision');a.static_mesh_component.set_editor_property('cast_shadow',False)
    a.set_actor_scale3d(u.Vector(*scale));return a
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
swords=sorted([a for a in actors.get_all_level_actors() if a.get_actor_label().endswith(' - Sabre')],key=lambda a:a.get_actor_label())
assert len(swords)==2
for idx,(sword,color) in enumerate(zip(swords,[(.03,.45,1.0),(1.0,.23,.015)]),1):
    tip=actor(f'Piste 1 - Colored tip {idx}',u.load_asset('/Engine/BasicShapes/Sphere'),mat('M_Tip_'+str(idx),color,False),(.05,.05,.05))
    tip.attach_to_component(sword.static_mesh_component,'',u.AttachmentRule.KEEP_RELATIVE,u.AttachmentRule.KEEP_RELATIVE,u.AttachmentRule.KEEP_RELATIVE,False)
    tip.set_actor_relative_location(u.Vector(96.5,0,0),False,False)
    opts=u.FbxImportUI()
    for k,v in {'import_mesh':True,'import_as_skeletal':False,'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH,'import_materials':False,'import_textures':False}.items():opts.set_editor_property(k,v)
    for k,v in {'combine_meshes':True,'auto_generate_collision':False,'convert_scene':True,'convert_scene_unit':True,'transform_vertex_to_absolute':True,'generate_lightmap_u_vs':False}.items():opts.static_mesh_import_data.set_editor_property(k,v)
    task=u.AssetImportTask()
    for k,v in {'filename':str(ROOT/f'SourceAssets/tip_trail_{idx}.fbx'),'destination_path':DEST,'destination_name':f'SM_TipTrail_{idx}','automated':True,'replace_existing':True,'save':True,'options':opts,'factory':u.FbxFactory()}.items():task.set_editor_property(k,v)
    assets.import_asset_tasks([task]);mesh=next(u.load_asset(p) for p in task.imported_object_paths if isinstance(u.load_asset(p),u.StaticMesh))
    actor(f'Piste 1 - One second trail {idx}',mesh,mat('M_Trail_'+str(idx),color,True))
seq=u.load_asset('/Game/GuansClub/Duel/LS_Piste01_Duel')
for tr in list(seq.get_tracks()):
    if isinstance(tr,u.MovieSceneMaterialParameterCollectionTrack) and tr.get_editor_property('mpc')==mpc:seq.remove_track(tr)
track=seq.add_track(u.MovieSceneMaterialParameterCollectionTrack);track.set_editor_property('mpc',mpc);track.set_display_name('Sword tip history - 1 second')
section=track.add_section();section.set_range(0,250)
rate=seq.get_tick_resolution();end_tick=round(250/24*rate.numerator/rate.denominator)
section.add_scalar_parameter_key('ReplaySeconds',u.FrameNumber(0),0,u.MovieSceneKeyInterpolation.LINEAR)
section.add_scalar_parameter_key('ReplaySeconds',u.FrameNumber(end_tick),250/24,u.MovieSceneKeyInterpolation.LINEAR)
u.EditorAssetLibrary.save_directory(DEST,only_if_is_dirty=False,recursive=True);u.EditorAssetLibrary.save_loaded_asset(seq);levels.save_current_level()
(ROOT/'tip_trails_setup.json').write_text(json.dumps({'history_seconds':1,'sample_rate':48,'tip_diameter_cm':5,'trail_diameter_cm':1.6,'colors':['blue','orange'],'loop_behavior':'clear history on restart','source':'sampled current sword geometry and animation; not measured real blade motion'},indent=2))
u.log('TIP_TRAILS_SETUP_COMPLETE')
