note = [[1,1,5,5,6,6,5], [0,0,0,0,0,0,0]]
octave = [[4,4,4,4,4,4,4], [4,4,4,4,4,4,4]]
duration = [4,4,4,4,4,4,8]

STATUS_PLAYING_SINGLE=1
STATUS_PLAYING_TOGETHER=2
STATUS_WAITING_ROLE=3
STATUS_WAITING_CONNECTION=4
STATUS_WAITING_BREAK=5
STATUS_WAITING_START=6

events:List[str]=[]
next_note_time=0
last_status=1
status=1
name="HexMo"
others_name="HexMo"
role="ALL"
last_str=""
ask_times=0
i=0
bpm=180

radio.set_group(55)
music.set_volume(255)
radio.set_transmit_power(7)


def append_a():
    """
    将按下按键A事件添加到事件队列
    """
    global events
    events.append("A:PUSH")


def append_b():
    """
    将按下按键B事件添加到事件队列
    """
    global events
    events.append("B:PUSH")


def append_l():
    """
    将按下LOGO事件添加到事件队列
    """
    global events
    events.append("L:PUSH")


def get_note_name(note_number):
    """
    获取音符名称
    """
    notes = ['r', 'C', 'D', 'E', 'F', 'G', 'A', 'B']
    return notes[note_number]


def play_note(number:int,play_as:str):
    """
    播放单个音符并返回当前音符长度(ms)
    """
    global note,octave,bpm
    if play_as=="ALL":
        if note[0][number]==0:
            note_now_int=note[1][number]
            octave_now=octave[1][number]
        else:
            note_now_int=note[0][number]
            octave_now=octave[0][number]
        #寻找非空音符
    elif play_as=="A":
        note_now_int=note[0][number]
        octave_now=octave[0][number]
    else:
        note_now_int=note[1][number]
        octave_now=octave[1][number]
    duration_now=duration[number]
    note_now_str=get_note_name(note_now_int)
    if note_now_str=='r':
        note_now='r:'+str(duration_now)
    else:
        note_now='HexMo'
        note_now=note_now_str+str(octave_now)+':'+str(duration_now)
    # serial.write_value("i",i)
    # serial.write_value("note_now_int", note_now_int)
    # serial.write_value("octave_now", octave_now)
    # serial.write_value("duration_now", duration_now)
    # serial.write_line("---------------------------------------------------")
    music.play(music.string_playable(note_now, bpm), music.PlaybackMode.IN_BACKGROUND)
    return int(60/bpm*1000*duration_now/4)


def keep_alive():
    """
    心跳保持连接
    """
    global events
    if status==STATUS_WAITING_CONNECTION or status==STATUS_WAITING_START:
        events.append("KEEP_ALIVE:S")


def send_name():
    """
    广播当前设备名称
    """
    global status,events
    if status==STATUS_WAITING_CONNECTION or status==STATUS_WAITING_START:
        events.append("SENT_NAME:XXX")


def deal_radio_massage_str(massage:str):
    """
    接收无线电消息
    """
    global events
    events.append(massage)


def update_screen(i):
    """
    更新屏幕
    """
    global status,role,others_name,last_str
    basic.clear_screen()
    tempstr=""
    if status==STATUS_PLAYING_TOGETHER or status==STATUS_PLAYING_SINGLE:
        leds=int(i*25/len(duration))
        for led_index in range(leds):
            if led_index < 25:
                x = led_index % 5
                y = led_index // 5
                led.plot(x, y)
    else:
        if status==STATUS_WAITING_ROLE:
            tempstr="PRESS BUTTON TO CONFIRM YOUR ROLE"
        elif status==STATUS_WAITING_BREAK:
            tempstr="ARE YOU SURE TO CUT DOWN CONNECTION?"
        elif status==STATUS_WAITING_CONNECTION:
            tempstr="NAME"+name+" WAITING FOR CONNECION"
        elif status==STATUS_WAITING_START:
            if role=="A":
                tempstr="CONNECTED,PRESS A TO PLAY OTHERS NAME:"+others_name
            else:
                tempstr="CONNECTED,PRESS A ON MICROBIT A TO PLAY"
        
        if not tempstr==last_str:
            # serial.write_line(tempstr)
            basic.show_string(tempstr,50)
            last_str=tempstr


def easteregg():
    global events
    events.append("ES:XXX")


def forever():
    global events,status,ask_times,i,last_status,last_str,name,others_name,role,next_note_time
    if i>=len(duration):
        i=0
    if control.millis()>=next_note_time and (status==STATUS_PLAYING_SINGLE or status==STATUS_PLAYING_TOGETHER):
        next_note_time=play_note(i, role)+control.millis()
        # serial.write_value("next_note_time", next_note_time)
        i+=1
        #触发音符播放
    while len(events)>0:
        #处理事件循环
        operation=events[0]
        events.pop(0)
        # serial.write_line(operation)
        temp=operation.split(":")
        operation_name=temp[0]
        operation_str=temp[1]
        if operation_name=="CB":
            #CB 连接断开
            radio.send_string("CB:XXX")
            last_status=status
            status=STATUS_PLAYING_SINGLE
            i=0
            next_note_time=control.millis()
            role="ALL"
            others_name="HexMo"
            ask_times=0
        if operation_name=="A":
            if status==STATUS_PLAYING_SINGLE:
                i=max(0,i-5)
                next_note_time=control.millis()+100
            elif status==STATUS_PLAYING_TOGETHER:
                pass
            elif status==STATUS_WAITING_BREAK:
                events.append("CB:XXX")
            elif status==STATUS_WAITING_ROLE:
                role="A"
                last_status=status
                status=STATUS_WAITING_CONNECTION
            elif status==STATUS_WAITING_CONNECTION:
                pass
            elif status==STATUS_WAITING_START:
                i=0
                next_note_time=control.millis()
                last_status=status
                radio.send_string("START:XXX")
                status=STATUS_PLAYING_TOGETHER
        if operation_name=="B":
            if status==STATUS_PLAYING_SINGLE:
                i=min(len(duration)-1,i+5)
                next_note_time=control.millis()+100
            elif status==STATUS_PLAYING_TOGETHER:
                last_status=status
                status=STATUS_WAITING_BREAK
            elif status==STATUS_WAITING_BREAK:
                status=last_status
            elif status==STATUS_WAITING_ROLE:
                role="B"
                last_status=status
                status=STATUS_WAITING_CONNECTION
            elif status==STATUS_WAITING_CONNECTION:
                pass
            elif status==STATUS_WAITING_START:
                last_status=status
                status=STATUS_WAITING_BREAK
                next_note_time=control.millis()+999999
        if operation_name=="L":
            if status==STATUS_PLAYING_SINGLE:
                last_status=status
                status=STATUS_WAITING_ROLE
            elif status==STATUS_WAITING_CONNECTION:
                last_status=status
                status=STATUS_PLAYING_SINGLE
        if operation_name=="START":
            #开始合奏
            last_status=status
            status=STATUS_PLAYING_TOGETHER
            ask_times=0
            i=0
            next_note_time=control.millis()
        if operation_name=="KEEP_ALIVE":
            if operation_str=="S":
                radio.send_string("KEEP_ALIVE:ASK")
                ask_times+=1
            if operation_str=="ASK":
                radio.send_string("KEEP_ALIVE:ANS")
                ask_times=0
            if operation_str=="ANS":
                ask_times=0
            if ask_times>=20:
                events.append("CB:XXX")
        if operation_name=="SENT_NAME":
            radio.send_string("NAME:"+role+name)
        if operation_name=="NAME" and status==STATUS_WAITING_CONNECTION:
            others_role=operation_str[:1]
            others_name=operation_str[1:]
            if not others_role==role:
                last_status=status
                status=STATUS_WAITING_START
                i=0
                next_note_time=control.millis()
        if operation_name=="ES":
            if randint(0, 2)==0:
                basic.clear_screen()
                basic.show_string("QAQ")
                basic.clear_screen()
            else:
                basic.pause(100)
                music.play(music.string_playable("E E D C D", 120), music.PlaybackMode.UNTIL_DONE)
                basic.pause(100)
    # serial.write_line(str(status))
    update_screen(i)

basic.forever(forever)
radio.on_received_string(deal_radio_massage_str)
loops.every_interval(2000,keep_alive)
loops.every_interval(500, send_name)
input.on_button_pressed(Button.A, append_a)
input.on_button_pressed(Button.B, append_b)
input.on_logo_event(TouchButtonEvent.PRESSED, append_l)
input.on_gesture(Gesture.SHAKE, easteregg)