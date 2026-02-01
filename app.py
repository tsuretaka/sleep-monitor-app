import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from models import init_db, SessionLocal, User, SleepLog, SleepSegment, Event
from datetime import datetime, date, time, timedelta
from pdf_generator import SleepPDFGenerator

# --- Initialize DB ---
init_db()

# --- Page Config ---
st.set_page_config(page_title="Sleep Monitor", layout="wide")

# --- Authentication ---
auth_file = "auth_config.yaml"
config = None

try:
    with open(auth_file) as file:
        config = yaml.load(file, Loader=SafeLoader)
except FileNotFoundError:
    # Try fetching from secrets if file not found (Cloud Deployment)
    if "credentials" in st.secrets:
        # Convert secrets to a mutable dictionary, as streamlit-authenticator tries to modify it
        config = dict(st.secrets)
        # Deep copy credentials to ensure mutability at nested levels if needed,
        # but configured dict usually suffices for top-level keys.
        # However, secrets object is recursive. Let's do a trick to ensure it's a dict.
        import json
        # Simple way to detach from AttrDict is via json dump/load or explicit dict conversion
        # Use simple dict conversion for top level, but for credentials we might need more.
        # Actually, stauth just needs to be able to set credentials['usernames']...
        # Let's try deep copy or recursive dict conversion.
        
        def to_dict(obj):
            if isinstance(obj, dict) or hasattr(obj, 'items'): # Check if it behaves like a dict
                return {k: to_dict(v) for k, v in obj.items()}
            return obj
            
        config = to_dict(st.secrets)
    else:
        st.error(f"{auth_file} not found and no secrets configuration detected.")
        st.stop()
except Exception as e:
    st.error(f"Auth error: {e}")
    st.stop()

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

authenticator.login('main')

# Retrieve status
authentication_status = st.session_state.get('authentication_status')
name = st.session_state.get('name')

if authentication_status is False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your username and password')
elif authentication_status:
    # --- Main App ---
    authenticator.logout('ログアウト', 'sidebar', key='unique_logout_key')
    st.sidebar.title(f"ようこそ、{name}さん")
    
    # DB Session
    db = SessionLocal()

    # --- Sync Config User to DB ---
    current_username = st.session_state.get('username')
    if current_username:
        user_in_db = db.query(User).filter(User.username == current_username).first()
        if not user_in_db:
            # Create user in DB if not exists (sync with auth_config)
            user_creds = config['credentials']['usernames'].get(current_username, {})
            new_db_user = User(
                username=current_username,
                email=user_creds.get('email', f"{current_username}@example.com"),
                password_hash=user_creds.get('password', 'stored_in_config'), # Placeholder
                display_name=user_creds.get('name', name)
            )
            db.add(new_db_user)
            db.commit()
            st.toast(f"ユーザーデータを初期化しました: {current_username}")
    
    # Navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "📅 カレンダー(月次確認)"
        
    options = ["📅 カレンダー(月次確認)", "📝 日次データ入力", "📄 PDF出力", "⚙️ 設定"]
    
    # Resolve index
    try:
        idx = options.index(st.session_state.current_page)
    except ValueError:
        idx = 0
        
    # Widget without Direct Key Binding for State
    selected_page = st.sidebar.radio("メニュー", options, index=idx)
    
    # Manual State Sync
    if selected_page != st.session_state.current_page:
        st.session_state.current_page = selected_page
        st.rerun()
        
    page = st.session_state.current_page
    
    import calendar

    if page == "📅 カレンダー(月次確認)":
        from streamlit_calendar import calendar
        st.title("月次レビュー")
        
        # Determine view date (default to today or stored state)
        if 'cal_date' not in st.session_state:
            st.session_state.cal_date = date.today()
            
        # Fetch data for a wider range to allow scrolling in calendar
        # Fetching +/- 60 days from current view date
        # Note: We use cal_date just as a reference, FullCalendar handles viewing
        start_date = st.session_state.cal_date - timedelta(days=60)
        end_date = st.session_state.cal_date + timedelta(days=60)

        logs = db.query(SleepLog).filter(
            SleepLog.user_id == 1,
            SleepLog.date >= start_date,
            SleepLog.date <= end_date
        ).all()
        
        events = []
        for log in logs:
            # Calc Sleep Time
            s_mins = 0
            for s in log.segments:
                if "Deep" in s.segment_type or "Doze" in s.segment_type:
                    try:
                        ts = datetime.strptime(s.start_at, "%H:%M")
                        te = datetime.strptime(s.end_at, "%H:%M")
                        d_s = datetime.combine(date.min, ts.time())
                        d_e = datetime.combine(date.min, te.time())
                        if d_e < d_s: d_e += timedelta(days=1)
                        s_mins += (d_e - d_s).total_seconds() / 60
                    except: pass
            
            h = int(s_mins // 60)
            m = int(s_mins % 60)
            
            title = f"{h}h{m}m"
            if log.sleepiness:
                title += f" Lv{log.sleepiness}"
            
            # Icons
            if log.events:
                evt_icons = ""
                for e in log.events:
                    if "alcohol" in e.event_type: evt_icons += "🍺"
                    elif "med" in e.event_type: evt_icons += "💊"
                    elif "caffeine" in e.event_type: evt_icons += "☕"
                    elif "bath" in e.event_type: evt_icons += "🛁"
                    elif "toilet" in e.event_type: evt_icons += "🚽"
                    else: evt_icons += "•"
                title += f" {evt_icons}"
                
            events.append({
                "title": title,
                "start": log.date.strftime("%Y-%m-%d"),
                "allDay": True,
                # Custom prop to identify date
                "extendedProps": {"date": log.date.strftime("%Y-%m-%d")}
            })

        calendar_options = {
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,listMonth" 
            },
            "initialDate": st.session_state.cal_date.strftime("%Y-%m-%d"),
            "navLinks": False,
            "selectable": True,
            "selectMirror": True,
            "dayMaxEvents": True,
            "contentHeight": "auto",
        }
        
        # Custom CSS to make events look like badges
        custom_css = """
        .fc-event-title {
            white-space: normal;
            font-size: 0.85em;
        }
        .fc-toolbar-title {
            font-size: 1.2em !important;
        }
        """

        cal = calendar(events=events, options=calendar_options, custom_css=custom_css, key="sleep_calendar")
        
        # Handle Event Click
        if cal.get("eventClick"):
            event = cal["eventClick"]["event"]
            # Extract date from start str (YYYY-MM-DD or ISO)
            clicked_date_str = event["start"].split("T")[0]
            try:
                clicked_date = datetime.strptime(clicked_date_str, "%Y-%m-%d").date()
                st.session_state.target_entry_date = clicked_date
                st.session_state.current_page = "📝 日次データ入力"
                st.rerun()
            except ValueError:
                pass
        
        # Handle Date Click (Empty cell click)
        if cal.get("dateClick"):
            date_click = cal["dateClick"]
            clicked_date_str = date_click["date"].split("T")[0]
            try:
                clicked_date = datetime.strptime(clicked_date_str, "%Y-%m-%d").date()
                st.session_state.target_entry_date = clicked_date
                st.session_state.current_page = "📝 日次データ入力"
                st.rerun()
            except ValueError:
                pass

        st.markdown("---")
        
    elif page == "📝 日次データ入力":
        st.title("日次データ入力")
        
        # 1. Date Selection
        default_date = date.today()
        if 'target_entry_date' in st.session_state:
            default_date = st.session_state.target_entry_date
            
        selected_date = st.date_input("日付選択", default_date)
        
        # Sync state if manually changed
        if selected_date != default_date:
            st.session_state.target_entry_date = selected_date
        
        # 2. Load existing data
        existing_log = db.query(SleepLog).filter(
            SleepLog.user_id == 1,
            SleepLog.date == selected_date
        ).first()
        
        # 3. Initialize Session State
        if 'current_date' not in st.session_state or st.session_state.current_date != selected_date:
            st.session_state.current_date = selected_date
            st.session_state.segments = []
            st.session_state.events = []
            st.session_state.sleepiness = 5
            st.session_state.memo = ""
            st.session_state.toilet_count = 0
            
            if existing_log:
                if existing_log.sleepiness: st.session_state.sleepiness = existing_log.sleepiness
                if existing_log.memo: st.session_state.memo = existing_log.memo
                if existing_log.toilet_count: st.session_state.toilet_count = existing_log.toilet_count
                
                # Load segments
                for seg in existing_log.segments:
                    try:
                        st.session_state.segments.append({
                            'start': datetime.strptime(seg.start_at, "%H:%M").time(),
                            'end': datetime.strptime(seg.end_at, "%H:%M").time(),
                            'type': seg.segment_type
                        })
                    except ValueError: pass
                    
                # Load events
                for evt in existing_log.events:
                    try:
                        st.session_state.events.append({
                            'time': datetime.strptime(evt.happened_at, "%H:%M").time(),
                            'type': evt.event_type
                        })
                    except ValueError: pass

        # 5. Input Forms
        # Helper for time selection (15 min intervals) to avoid mobile keyboard popup
        time_options = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 15, 30, 45)]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("睡眠区間の追加")
            with st.form("add_segment_form", clear_on_submit=True):
                s_type = st.selectbox("種類", ["In-bed (布団に入っている)", "Deep Sleep (ぐっすり)", "Doze (うとうと)", "Awake (眠れない)"])
                
                # Use selectbox for time to improve mobile UX
                def get_time_index(t_str):
                    try: return time_options.index(t_str)
                    except ValueError: return 0
                
                t_start_str = st.selectbox("開始時刻", time_options, index=get_time_index("23:00"))
                t_end_str = st.selectbox("終了時刻", time_options, index=get_time_index("07:00"))

                t_start = datetime.strptime(t_start_str, "%H:%M").time()
                t_end = datetime.strptime(t_end_str, "%H:%M").time()
                
                if st.form_submit_button("区間を追加"):
                    st.session_state.segments.append({
                        'type': s_type,
                        'start': t_start,
                        'end': t_end
                    })
                    st.rerun()

        with col2:
            st.subheader("イベントの追加")
            with st.form("add_event_form", clear_on_submit=True):
                e_type = st.selectbox("イベント種類", ["sleep_med (睡眠薬)", "toilet (トイレ)", "other_med (その他薬)"])
                
                e_time_str = st.selectbox("発生時刻", time_options, index=get_time_index("22:00"))
                e_time = datetime.strptime(e_time_str, "%H:%M").time()
                
                if st.form_submit_button("イベントを追加"):
                    st.session_state.events.append({
                        'type': e_type,
                        'time': e_time
                    })
                    st.rerun()

        st.subheader("日次情報")
        # Removed Toilet Count Input, Keep Sleepiness and Memo
        st.session_state.sleepiness = st.slider("起床時の眠気 (1-10)", 1, 10, st.session_state.sleepiness)
        
        # Memo input - use key to bind directly if possible, or manual update
        new_memo = st.text_area("特記事項(メモ)", value=st.session_state.memo, height=100)
        st.session_state.memo = new_memo # Update state immediately

        # Remove Item Managements
        if st.session_state.segments or st.session_state.events:
            with st.expander("追加項目の管理（削除）"):
                if st.session_state.segments:
                    st.markdown("**睡眠区間**")
                    for i, seg in enumerate(st.session_state.segments):
                        col_del, col_info = st.columns([1, 4])
                        if col_del.button("削除", key=f"del_seg_{i}"):
                            st.session_state.segments.pop(i)
                            st.rerun()
                        col_info.text(f"{seg['type']} ({seg['start'].strftime('%H:%M')} ~ {seg['end'].strftime('%H:%M')})")
                
                if st.session_state.events:
                    st.markdown("**イベント**")
                    for i, evt in enumerate(st.session_state.events):
                        col_del, col_info = st.columns([1, 4])
                        if col_del.button("削除", key=f"del_evt_{i}"):
                            st.session_state.events.pop(i)
                            st.rerun()
                        col_info.text(f"{evt['type']} at {evt['time'].strftime('%H:%M')}")

        # Save Button
        if st.button("日次データを保存", type="primary"):
            # 1. Create or Update SleepLog
            log = existing_log
            if not log:
                log = SleepLog(user_id=1, date=selected_date)
                db.add(log)
                db.commit() 
                db.refresh(log)
            
            # Auto-calculate toilet count from events
            toilet_c = 0
            for e in st.session_state.events:
                if "toilet" in e['type']:
                    toilet_c += 1
            
            # Update info
            log.sleepiness = st.session_state.sleepiness
            log.memo = st.session_state.memo
            log.toilet_count = toilet_c
            
            # 2. Replace Segments/Events
            for s in log.segments: db.delete(s)
            for e in log.events: db.delete(e)
            
            for s in st.session_state.segments:
                new_seg = SleepSegment(
                    log_id=log.id,
                    segment_type=s['type'],
                    start_at=s['start'].strftime("%H:%M"),
                    end_at=s['end'].strftime("%H:%M")
                )
                db.add(new_seg)
                
            for e in st.session_state.events:
                new_evt = Event(
                    log_id=log.id,
                    event_type=e['type'],
                    happened_at=e['time'].strftime("%H:%M")
                )
                db.add(new_evt)
                
            db.commit()
            st.success("保存しました！")
            st.rerun() # Force reload to show updated summary

        st.markdown("---")

        # 4. Registered Data Summary (Text Based) - MOVED TO BOTTOM
        st.subheader(f"{selected_date.strftime('%Y/%m/%d')} の登録データ概要")
        
        summ_col1, summ_col2 = st.columns(2)
        
        with summ_col1:
            st.markdown("##### 🛌 睡眠区間")
            if st.session_state.segments:
                seg_map = {
                    "In-bed": "布団内",
                    "Deep Sleep": "ぐっすり",
                    "Doze": "うとうと",
                    "Awake": "覚醒"
                }
                # Format for display
                seg_display = []
                for s in st.session_state.segments:
                    raw_type = s['type'].split("(")[0].strip()
                    jp_type = seg_map.get(raw_type, raw_type)
                    
                    seg_display.append({
                        "種類": jp_type,
                        "開始": s['start'].strftime("%H:%M"),
                        "終了": s['end'].strftime("%H:%M")
                    })
                st.table(seg_display)
            else:
                st.info("データなし")

        with summ_col2:
            st.markdown("##### 📍 イベント")
            if st.session_state.events:
                evt_map = {
                    "sleep_med": "睡眠薬",
                    "toilet": "トイレ",
                    "other_med": "その他薬",
                    "alcohol": "飲酒",
                    "caffeine": "カフェイン",
                    "bath": "入浴"
                }
                evt_display = []
                for e in st.session_state.events:
                    raw_type = e['type'].split("(")[0].strip()
                    jp_type = evt_map.get(raw_type, raw_type)
                    
                    evt_display.append({
                        "種類": jp_type,
                        "時刻": e['time'].strftime("%H:%M")
                    })
                st.table(evt_display)
            else:
                st.info("データなし")
        
        # Metrics Summary
        st.markdown("##### 📝 日次情報確認")
        
        # Calculate toilet count for display
        display_toilet_count = 0
        if st.session_state.events:
             for e in st.session_state.events:
                if "toilet" in e['type']:
                    display_toilet_count += 1
                    
        m_col1, m_col2, m_col3, m_col4 = st.columns([1, 1, 1, 3])
        
        # Calculate Sleep Duration for Display
        disp_sleep_mins = 0
        for s in st.session_state.segments:
            if "Deep" in s['type'] or "Doze" in s['type']:
                try:
                    # s['start'] and s['end'] are time objects
                    # Need full datetime for calc
                    d_s = datetime.combine(date.min, s['start'])
                    d_e = datetime.combine(date.min, s['end'])
                    if d_e < d_s:
                        d_e += timedelta(days=1)
                    disp_sleep_mins += (d_e - d_s).total_seconds() / 60
                except:
                   pass
        
        disp_hours = int(disp_sleep_mins // 60)
        disp_mins = int(disp_sleep_mins % 60)
        disp_sleep_str = f"{disp_hours}h {disp_mins}m"

        m_col1.metric("眠気", st.session_state.sleepiness)
        m_col2.metric("睡眠時間", disp_sleep_str)
        m_col3.metric("トイレ回数", display_toilet_count)
        m_col4.text_area("メモ内容", value=st.session_state.memo, disabled=True, height=68, key="memo_display")

    elif page == "📄 PDF出力":
        st.title("PDF出力")
        
        st.markdown("### 1. キャリブレーション (位置調整用)")
        st.caption("テストデータを使ってPDFのレイアウトを確認します。")
        
        if st.button("キャリブレーションPDFを生成"):
            gen = SleepPDFGenerator()
            output_path = "calibration_grid.pdf"
            
            # Use Dummy Data to verify "blue bar" visibility
            dummy_data = [{
                'day_index': 0, # Day 1
                'start_hour': 6.0,
                'end_hour': 12.0,
                'type': 'Calibration'
            }]
            
            # Dummy Daily Logs + Events + Header for Calibration
            dummy_daily_logs = {
                0: {
                    'sleepiness': 7,
                    'memo': 'これはテスト用の長いメモです。折り返し確認用テキスト。',
                    'events': [
                        {'time': 22.0, 'type': 'sleep_med'}, # ▲ at 22:00
                        {'time': 2.5, 'type': 'toilet'}      # ▽ at 2:30 (next day side)
                    ]
                }
            }
            dummy_user_info = {'name': 'Test User', 'id': '001', 'year': 2026, 'month': 2}
            
            # Pass dummy data
            gen.generate(dummy_data, dummy_daily_logs, dummy_user_info, output_path, debug=True)
                 
            with open(output_path, "rb") as f:
                st.download_button(
                    label="Download Calibration PDF",
                    data=f,
                    file_name="calibration_grid.pdf",
                    mime="application/pdf"
                )
            st.success("Calibration PDF generated!")

        st.markdown("---")
        st.markdown("### 2. Monthly Report")
        target_month = st.date_input("Target Month", date.today())
        
        if st.button("Generate Monthly Report"):
             # 1. Fetch Data
             start_date = target_month.replace(day=1)
             next_month = start_date.replace(day=28) + timedelta(days=4)
             end_date = next_month - timedelta(days=next_month.day)
             
             logs = db.query(SleepLog).filter(
                 SleepLog.user_id == 1, 
                 SleepLog.date >= start_date,
                 SleepLog.date <= end_date
             ).all()
             
             pdf_data = []
             daily_logs = {}
             
             for log in logs:
                 day_index = log.date.day - 1 # 0-indexed (1st = 0)
                 
                 # Prepare Daily Metrics
                 d_events = []
                 for evt in log.events:
                     try:
                         et = datetime.strptime(evt.happened_at, "%H:%M").time()
                         et_float = et.hour + et.minute/60.0
                         d_events.append({'time': et_float, 'type': evt.event_type})
                     except ValueError:
                         continue
                 
                 # Calculate Total Sleep Time (Deep + Doze)
                 total_minutes = 0
                 for seg in log.segments:
                     if "Deep" in seg.segment_type or "Doze" in seg.segment_type:
                         try:
                             t_s = datetime.strptime(seg.start_at, "%H:%M").time()
                             t_e = datetime.strptime(seg.end_at, "%H:%M").time()
                             
                             dt_s = datetime.combine(date.min, t_s)
                             dt_e = datetime.combine(date.min, t_e)
                             
                             if t_e < t_s:
                                 dt_e += timedelta(days=1)
                                 
                             duration = (dt_e - dt_s).total_seconds() / 60
                             total_minutes += duration
                         except ValueError:
                             continue
                 
                 # Format Duration
                 hours = int(total_minutes // 60)
                 mins = int(total_minutes % 60)
                 duration_str = f"睡眠時間: {hours}h{mins:02d}m"
                 
                 daily_logs[day_index] = {
                     'sleepiness': log.sleepiness,
                     'memo': log.memo, # Keep original memo
                     'total_sleep': duration_str, # Pass separately
                     'events': d_events
                 }
                 
                 for seg in log.segments:
                     
                     # Parse stored string times back to time objects
                     try:
                         t_s = datetime.strptime(seg.start_at, "%H:%M").time()
                         t_e = datetime.strptime(seg.end_at, "%H:%M").time()
                     except ValueError:
                         continue # Skip malformed data

                     def time_to_float(t):
                         return t.hour + t.minute/60.0
                     
                     s_h = time_to_float(t_s)
                     e_h = time_to_float(t_e)
                     
                     # Check for midnight crossing
                     if e_h < s_h:
                         # Split into two segments
                         
                         # 1. Start Time to 24:00 (Current Day)
                         pdf_data.append({
                             'day_index': day_index,
                             'start_hour': s_h,
                             'end_hour': 24.0,
                             'type': seg.segment_type
                         })
                         
                         # 2. 0:00 to End Time (Same Day, Left side)
                         pdf_data.append({
                             'day_index': day_index, # Keep same day
                             'start_hour': 0.0,
                             'end_hour': e_h,
                             'type': seg.segment_type
                         })
                     else:
                         # Normal segment (Same day)
                         pdf_data.append({
                             'day_index': day_index,
                             'start_hour': s_h,
                             'end_hour': e_h,
                             'type': seg.segment_type
                         })
             
             # 2. Generate
             gen = SleepPDFGenerator()
             
             # Fetch user info for header
             current_username = st.session_state.get("username")
             current_user = db.query(User).filter(User.username == current_username).first()
             u_name = current_user.display_name if current_user and current_user.display_name else (current_username or "User")
             u_id = current_user.header_user_id if current_user and current_user.header_user_id else ""
             
             user_info = {
                 'name': u_name, 
                 'id': u_id, 
                 'year': target_month.year, 
                 'month': target_month.month
             }
             
             output_path = f"report_{target_month.strftime('%Y_%m')}.pdf"
             gen.generate(pdf_data, daily_logs, user_info, output_path, debug=False)
             
             with open(output_path, "rb") as f:
                st.download_button(
                    label="月次レポートをダウンロード",
                    data=f,
                    file_name=output_path,
                    mime="application/pdf"
                )
             st.success(f"{target_month.strftime('%Y-%m')} のレポートを作成しました！")

    elif page == "⚙️ 設定":
        st.title("設定")
        st.subheader("ユーザープロフィール設定")
        
        current_username = st.session_state.get("username")
        current_user = db.query(User).filter(User.username == current_username).first()
        
        if current_user:
            with st.form("profile_settings"):
                new_display_name = st.text_input("表示用氏名 (PDFヘッダー)", value=current_user.display_name if current_user.display_name else "")
                new_header_id = st.text_input("表示用ID (PDFヘッダー)", value=current_user.header_user_id if current_user.header_user_id else "")
                
                if st.form_submit_button("保存"):
                    current_user.display_name = new_display_name
                    current_user.header_user_id = new_header_id
                    db.commit()
                    st.success("設定を更新しました！")
                    st.rerun()
        else:
            st.error(f"ユーザー情報が見つかりません。(Username: {current_username})")
