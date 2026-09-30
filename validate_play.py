import unreal as u
import time, json, traceback
from pathlib import Path
ROOT=Path(u.Paths.project_dir()).resolve()
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
u.EditorPythonScripting.set_keep_python_script_alive(True)
levels.load_level('/Game/GuansClub/FencingHall')
u.SystemLibrary.execute_console_command(editor.get_editor_world(),'t.MaxFPS 30')
levels.editor_request_begin_play()
state={'phase':'settle','time':time.monotonic()}
report={}

def xyz(p): return [p.x,p.y,p.z]

def finish(error=None):
    if error: report['error']=error
    report['status']='failed' if error else 'passed'
    (ROOT/'play_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    u.log('GUANS_PLAY_VALIDATION '+json.dumps(report))
    u.unregister_slate_post_tick_callback(handle)
    levels.editor_request_end_play()
    u.EditorPythonScripting.set_keep_python_script_alive(False)

def tick(dt):
    try:
        elapsed=time.monotonic()-state['time']
        world=editor.get_game_world()
        if state['phase']=='settle':
            if elapsed<10: return
            assert world, 'PIE world did not start'
            pawn=u.GameplayStatics.get_player_character(world,0)
            pc=u.GameplayStatics.get_player_controller(world,0)
            assert pawn and pc, 'First person pawn/controller missing'
            report['pawn_class']=pawn.get_class().get_path_name()
            report['spawn']=xyz(pawn.get_actor_location())
            assert 70<pawn.get_actor_location().z<150, 'Pawn did not settle on floor'
            subs=[s for s in u.ObjectIterator(u.EnhancedInputLocalPlayerSubsystem) if s.get_outer().get_class().get_name()=='LocalPlayer']
            assert len(subs)==1, f'Expected one local input subsystem, got {len(subs)}'
            sub=subs[0]
            assert sub, 'Enhanced input subsystem missing'
            state.update(pawn=pawn,pc=pc,sub=sub,move=u.load_asset('/Game/Input/Actions/IA_Move'),look=u.load_asset('/Game/Input/Actions/IA_MouseLook'),phase='move',time=time.monotonic())
            u.log('GUANS_VALIDATION_MOVING')
        elif state['phase']=='move':
            state['sub'].inject_input_vector_for_action(state['move'],u.Vector(0,1,0),[],[])
            if elapsed>2:
                p=state['pawn'].get_actor_location()
                report['after_forward']=xyz(p)
                assert p.x>report['spawn'][0]+100, 'Forward input did not move pawn'
                state.update(phase='turn',time=time.monotonic(),yaw=state['pc'].get_control_rotation().yaw)
        elif state['phase']=='turn':
            state['sub'].inject_input_vector_for_action(state['look'],u.Vector(1,0,0),[],[])
            if elapsed>1:
                report['look_yaw_change']=state['pc'].get_control_rotation().yaw-state['yaw']
                assert abs(report['look_yaw_change'])>2, 'Look input did not turn camera'
                state['pawn'].set_actor_location(u.Vector(1100,0,100),False,True)
                state['pc'].set_control_rotation(u.Rotator(0,0,0))
                state.update(phase='wall',time=time.monotonic())
        elif state['phase']=='wall':
            state['sub'].inject_input_vector_for_action(state['move'],u.Vector(0,1,0),[],[])
            if elapsed>2:
                p=state['pawn'].get_actor_location()
                report['wall_stop']=xyz(p)
                assert 1150<p.x<1290 and 70<p.z<150, 'Wall or floor collision failed'
                state['pawn'].set_actor_location(u.Vector(-1080,0,100),False,True)
                state['pc'].set_control_rotation(u.Rotator(0,0,0))
                state.update(phase='screenshot',time=time.monotonic())
        elif state['phase']=='screenshot' and elapsed>4:
            u.AutomationLibrary.take_high_res_screenshot(1280,800,str(ROOT/'ue_walkthrough.png'))
            state.update(phase='finish',time=time.monotonic())
        elif state['phase']=='finish' and elapsed>6:
            report['screenshot_exists']=(ROOT/'ue_walkthrough.png').exists()
            finish()
    except Exception:
        finish(traceback.format_exc())

handle=u.register_slate_post_tick_callback(tick)
