from pathlib import Path
import subprocess
import sys
Q=Path(__file__).resolve().parents[2];P=Path(sys.argv[1]).resolve();P.mkdir(parents=True,exist_ok=True)
def fn(file,name):
 s=(Q/file).read_text();at=s.index(name+'(');start=s.rfind('\n',0,s.rfind('\n',0,at))+1 if False else s.rfind('\n',0,at)+1
 end=s.index('{',at);level=1;i=end+1
 while level:
  if s[i]=='{':level+=1
  if s[i]=='}':level-=1
  i+=1
 return s[start:i]
source='''#include <assert.h>
#include <stdbool.h>
#include <string.h>
#include <stddef.h>
#include <stdio.h>
#define container_of(ptr,type,member) ((type*)((char*)(ptr)-offsetof(type,member)))
#define RUN_STATE_SUSPENDED 1
#define RUN_STATE_PAUSED 2
#define SHUTDOWN_ACTION_POWEROFF 3
#define SHUTDOWN_CAUSE_HOST_UI 4
#define ACPI_BITMASK_SLEEP_BUTTON_ENABLE 0x200
#define ACPI_BITMASK_SLEEP_BUTTON_STATUS 0x200
#define error_report(...) (++errors)
#define trace_apple_gfx_close_request(action) assert(apple_gfx_close_action_valid(action))
typedef struct Notifier { int dummy; } Notifier;
typedef struct Display { void *pgdisp; } Display;
typedef struct AppleGFXState { char *close_action; bool sleep_requested,suspended; void *pgdev; unsigned num_displays; Display displays[2]; Notifier suspend_notifier,wakeup_notifier; } AppleGFXState;
static int shutdown_action, off,down,sleep_requests,pauses,unpauses,markers,errors,sci_updates;
static bool actual_suspended,accepted,last_marker,running=true;
static int prepared,vmstops,notifications;
static bool runstate_is_running(void){return running;}
static void qemu_system_vmstop_request_prepare(void){++prepared;}
static void qemu_system_vmstop_request(int state){assert(state==RUN_STATE_PAUSED);++vmstops;}
static void qapi_event_send_powerdown(void){++notifications;}
static bool runstate_check(int x){assert(x==1);return actual_suspended;}
static void qemu_system_shutdown_request(int x){assert(x==4);++off;}
static void qemu_system_powerdown_request(void){++down;}
static bool qemu_system_sleep_button_request(void){++sleep_requests;return accepted;}
static void rvg_device_pause(void *x){assert(x);++pauses;}
static void rvg_device_unpause(void *x){assert(x);++unpauses;}
static void rvg_display_set_window_suspended(void *x,bool z){assert(x);++markers;last_marker=z;}
typedef struct Regs Regs;
struct Regs { struct { struct { unsigned en,sts; } evt; } pm1; struct { void (*update_sci)(Regs*); } tmr; };
typedef struct ICH9LPCPMRegs { Notifier sleep_button_notifier; bool sleep_button,disable_s3; Regs acpi_regs; } ICH9LPCPMRegs;
static void update_sci(Regs *x){assert(x->pm1.evt.sts&0x200);++sci_updates;}
'''
for name in ['apple_gfx_close_action_valid','apple_gfx_input_close','apple_gfx_suspend','apple_gfx_wakeup']:source+=fn('hw/display/apple-gfx.c',name)+'\n'
source+=fn('hw/acpi/ich9.c','pm_sleep_button_req')+'\n'
source+='''int main(void) {
 AppleGFXState s={.pgdev=(void*)1,.num_displays=1,.displays={{.pgdisp=(void*)2}}};
 assert(apple_gfx_close_action_valid(NULL));
 assert(apple_gfx_close_action_valid("poweroff"));assert(apple_gfx_close_action_valid("powerdown"));assert(apple_gfx_close_action_valid("suspend"));assert(!apple_gfx_close_action_valid("typo"));
 apple_gfx_input_close(&s);assert(off==1&&shutdown_action==3);
 s.close_action="powerdown";apple_gfx_input_close(&s);apple_gfx_input_close(&s);assert(down==2&&off==1);
 actual_suspended=true;apple_gfx_input_close(&s);assert(down==2&&off==1&&errors==1);
 actual_suspended=false;s.close_action="suspend";apple_gfx_input_close(&s);assert(sleep_requests==1&&!s.sleep_requested&&off==1&&pauses==0);
 accepted=true;apple_gfx_input_close(&s);apple_gfx_input_close(&s);assert(sleep_requests==3&&s.sleep_requested&&pauses==0);
 actual_suspended=true;apple_gfx_suspend(&s.suspend_notifier,NULL);apple_gfx_suspend(&s.suspend_notifier,NULL);assert(pauses==1&&s.suspended&&markers==1&&last_marker);
 apple_gfx_input_close(&s);assert(sleep_requests==3&&off==1);
 apple_gfx_wakeup(&s.wakeup_notifier,NULL);apple_gfx_wakeup(&s.wakeup_notifier,NULL);assert(unpauses==1&&!s.suspended&&!s.sleep_requested&&markers==2&&!last_marker);
 s.close_action="pause";actual_suspended=false;
 apple_gfx_input_close(&s);assert(prepared==1&&vmstops==1&&notifications==1&&down==2&&off==1&&sleep_requests==3);
 running=false;apple_gfx_input_close(&s);assert(prepared==1&&vmstops==1&&notifications==2&&down==2&&off==1);
 ICH9LPCPMRegs pm={0};pm.acpi_regs.tmr.update_sci=update_sci;bool ok=false;
 pm_sleep_button_req(&pm.sleep_button_notifier,&ok);assert(!ok&&sci_updates==0);
 pm.sleep_button=true;pm_sleep_button_req(&pm.sleep_button_notifier,&ok);assert(!ok&&sci_updates==0);
 pm.acpi_regs.pm1.evt.en=0x200;pm.disable_s3=true;pm_sleep_button_req(&pm.sleep_button_notifier,&ok);assert(!ok&&sci_updates==0);
 pm.disable_s3=false;pm_sleep_button_req(&pm.sleep_button_notifier,&ok);assert(ok&&sci_updates==1&&pm.acpi_regs.pm1.evt.sts==0x200);
 puts("PASS actual close handlers: default, repeated powerdown, suspended powerdown refusal, cooperative sleep, idempotent pause/wake; ACPI opt-in/guest-enabled/S3-enabled");
}'''
(P/'test-qemu-policy.c').write_text(source)
subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-parameter',str(P/'test-qemu-policy.c'),'-o',str(P/'test-qemu-policy')],check=True)
subprocess.run([str(P/'test-qemu-policy')],check=True)
