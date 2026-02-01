
import random
from datetime import datetime, timedelta, date, time
from sqlalchemy.orm import Session
from models import engine, User, SleepLog, SleepSegment, Event, SessionLocal

def populate_data():
    session = SessionLocal()
    
    # 1. Get or Create User 'user1'
    username = "user1"
    user = session.query(User).filter(User.username == username).first()
    if not user:
        print(f"Creating user: {username}")
        user = User(
            username=username,
            email="user1@example.com",
            password_hash="hashed_secret", # Mock
            display_name="テスト 太郎",
            header_user_id="ID-001"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    else:
        print(f"Found user: {user.username}")
        # Ensure display info is set for PDF test
        if not user.display_name:
            user.display_name = "テスト 太郎"
            user.header_user_id = "ID-001"
            session.commit()

    # 2. Define Date Range (Feb 2026)
    start_date = date(2026, 2, 1)
    end_date = date(2026, 2, 28)
    
    # Segment Types
    TYPE_IN_BED = "In-bed (布団に入っている)"
    TYPE_DEEP = "Deep Sleep (ぐっすり)"
    TYPE_DOZE = "Doze (うとうと)"
    TYPE_AWAKE = "Awake (眠れない)"
    
    # Clear existing logs for this period to avoid duplicates
    existing_logs = session.query(SleepLog).filter(
        SleepLog.user_id == user.id,
        SleepLog.date >= start_date,
        SleepLog.date <= end_date
    ).all()
    for log in existing_logs:
        session.delete(log)
    session.commit()
    print("Cleared existing logs for Feb 2026.")

    # 3. Generate Data
    current_date = start_date
    while current_date <= end_date:
        print(f"Generating data for {current_date}...")
        
        # --- Base Times ---
        # Bedtime: 22:00 ~ 00:00
        bed_hour = random.randint(22, 23)
        bed_min = random.choice([0, 15, 30, 45])
        
        # Wake time: 06:00 ~ 08:00 (Next day usually, but we store times relative to log date)
        # Note: In this app, times crossing midnight are handled. 
        # But for segments, we usually specify start/end.
        # Let's say Bedtime is usually on Previous Day? 
        # Wait, app treats "Date" as the main date. usually sleep starts previous night.
        # But let's assume simple logic: 
        # 23:00 (on day X) -> 07:00 (on day X+1)
        # However, the input UI allows typing 23:00 and 07:00.
        
        bed_time_obj = time(bed_hour, bed_min)
        wake_hour = random.randint(6, 8)
        wake_min = random.choice([0, 15, 30, 45])
        wake_time_obj = time(wake_hour, wake_min)
        
        # --- Create Log ---
        log = SleepLog(
            user_id=user.id,
            date=current_date,
            sleepiness=random.randint(2, 8),
            memo=random.choice([
                "よく眠れた。", "少し途中覚醒があった。", "夢を見た。", 
                "朝スッキリ目覚めた。", "なかなか寝付けなかった。", ""
            ]),
            toilet_count=0 # Calculated later
        )
        session.add(log)
        session.commit() # Get ID
        
        # --- Segments ---
        # 1. Base In-bed (Arrow)
        seg_inbed = SleepSegment(
            log_id=log.id,
            segment_type=TYPE_IN_BED,
            start_at=bed_time_obj.strftime("%H:%M"),
            end_at=wake_time_obj.strftime("%H:%M")
        )
        session.add(seg_inbed)
        
        # 2. Main Sleep Segments (Complex Pattern)
        # Sequence: Deep -> Doze -> Awake -> Deep
        
        # Calculate full sleep duration timestamps
        # In-bed Start + 15min -> In-bed End - 15min
        sleep_start_dt = datetime.combine(date.today(), bed_time_obj) + timedelta(minutes=15)
        sleep_end_dt = datetime.combine(date.today() + timedelta(days=1), wake_time_obj) - timedelta(minutes=15)
        
        # We'll create distinct blocks to ensure all types show up.
        # Block 1: Deep Sleep (First 2 hours)
        b1_end = sleep_start_dt + timedelta(hours=2)
        
        # Block 2: Doze (Next 1 hour)
        b2_end = b1_end + timedelta(hours=1)
        
        # Block 3: Awake (Next 30 mins)
        b3_end = b2_end + timedelta(minutes=30)
        
        # Block 4: Deep Sleep (Rest of the time)
        
        # Safeguard: Ensure we don't exceed end time
        if b3_end >= sleep_end_dt:
             # If sleep is too short, just do simple splits
             # Fallback to simple Deep Sleep
             seg_deep = SleepSegment(
                log_id=log.id,
                segment_type=TYPE_DEEP,
                start_at=sleep_start_dt.strftime("%H:%M"),
                end_at=sleep_end_dt.strftime("%H:%M") 
             )
             session.add(seg_deep)
        else:
             # Add segments
             # 1. Deep
             session.add(SleepSegment(
                log_id=log.id, segment_type=TYPE_DEEP,
                start_at=sleep_start_dt.strftime("%H:%M"), end_at=b1_end.strftime("%H:%M")
             ))
             
             # 2. Doze
             session.add(SleepSegment(
                log_id=log.id, segment_type=TYPE_DOZE,
                start_at=b1_end.strftime("%H:%M"), end_at=b2_end.strftime("%H:%M")
             ))
             
             # 3. Awake
             session.add(SleepSegment(
                log_id=log.id, segment_type=TYPE_AWAKE,
                start_at=b2_end.strftime("%H:%M"), end_at=b3_end.strftime("%H:%M")
             ))
             
             # 4. Deep (Remaining)
             session.add(SleepSegment(
                log_id=log.id, segment_type=TYPE_DEEP,
                start_at=b3_end.strftime("%H:%M"), end_at=sleep_end_dt.strftime("%H:%M")
             ))
             
        # --- Random Nap (Daytime Sleep) ---
        # Add a nap on approx 8 days (~30%)
        if random.random() < 0.3:
            nap_start_hour = random.randint(13, 15)
            nap_start_min = random.choice([0, 30])
            nap_duration = random.choice([30, 60, 90])
            
            nap_start = time(nap_start_hour, nap_start_min)
            nap_start_dt = datetime.combine(current_date, nap_start)
            nap_end_dt = nap_start_dt + timedelta(minutes=nap_duration)
            
            # Nap consists of Doze type (Upper bar)
            # Optionally add In-bed if they slept in bed, but for nap often just Doze is fine.
            # Let's add Doze only to test visualization of detached segments.
            seg_nap = SleepSegment(
                log_id=log.id,
                segment_type=TYPE_DOZE,
                start_at=nap_start_dt.strftime("%H:%M"),
                end_at=nap_end_dt.strftime("%H:%M")
            )
            session.add(seg_nap)
            
        # --- Events ---
        # 1. Sleep Med (Before Bed)
        if random.random() < 0.3:
            med_time = (datetime.combine(date.today(), bed_time_obj) - timedelta(minutes=30)).time()
            evt_med = Event(
                log_id=log.id,
                event_type="sleep_med (睡眠薬)",
                happened_at=med_time.strftime("%H:%M")
            )
            session.add(evt_med)
            
        # 2. Toilet (During night)
        toilet_c = 0
        if random.random() < 0.3:
            t_time = time(random.randint(1, 4), random.choice([0, 30]))
            evt_toilet = Event(
                log_id=log.id,
                event_type="toilet (トイレ)",
                happened_at=t_time.strftime("%H:%M")
            )
            session.add(evt_toilet)
            toilet_c += 1
            
        log.toilet_count = toilet_c
        session.commit()
        
        current_date += timedelta(days=1)
        
    session.close()
    print("Data population complete!")

if __name__ == "__main__":
    populate_data()
