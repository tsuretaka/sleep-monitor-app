import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black, red, blue
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Register Japanese Font
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))

# Constants for A4 Portrait calculated in points (1pt = 1/72 inch)
PAGE_WIDTH, PAGE_HEIGHT = A4

class SleepPDFGenerator:
    def __init__(self):
        self.packet = io.BytesIO()
        self.template_path = "assets/template.png"
        
        # Template Image Dimensions (PX) - Measured from file
        self.IMG_WIDTH = 1584
        self.IMG_HEIGHT = 2242
        
        # --- Layout Configuration (Pixel Coordinates) ---
        # User will provide precise PX values from the debug grid.
        # These are ESTIMATES based on previous MM values converted to PX.
        # 1mm approx 5.9 px vertically (2242 / 297mm approx 7.5px/mm? Wait.)
        # A4 height 297mm. Img height 2242px. 1mm = 7.54 px.
        # Y_START approx 279.5mm -> approx 2108 px from BOTTOM?
        # Image coords are from TOP.
        # 297 - 279.5 = 17.5mm from top.
        # 17.5mm * 7.54 = 132 px from top.
        
        # --- Layout Configuration (Pixel Coordinates) ---
        # Time Axis X Coordinates (PX)
        self.X_TIME_START_PX = 217
        self.X_TIME_END_PX = 1185
        
        self.TIME_START_NOTATION = 0.0 
        self.TIME_END_NOTATION = 24.0
        
        # Right Columns X Coordinates
        self.X_SLEEPINESS_START = 1230
        self.X_NOTE_START = 1300
        self.X_NOTE_WIDTH = 250
        
        # Header Coordinates
        self.HEADER_ID_X = 550
        self.HEADER_NAME_X = 830
        self.HEADER_YEAR_X = 1089
        self.HEADER_MONTH_X = 1200
        self.HEADER_Y_PX = 70 

        # --- Y Coordinates for Each Day (Top of the row) ---
        # Manually calibrated Y positions for 31 days.
        # Values updated based on user measurement (Step 1378)
        self.DAILY_Y_STARTS = [
            149, 212, 272, 333, 394,  # 1-5
            457, 519, 582, 644, 706,  # 6-10
            767, 830, 892, 955, 1015, # 11-15
            1080, 1140, 1202, 1264, 1328, # 16-20
            1388, 1450, 1512, 1575, 1638, # 21-25
            1701, 1762, 1824, 1884, 1948, # 26-30
            2009                          # 31
        ]

    def _px_to_pdf_x(self, px):
        """Convert Image Pixel X to PDF Point X"""
        return px * (PAGE_WIDTH / self.IMG_WIDTH)

    def _px_to_pdf_y(self, px):
        """Convert Image Pixel Y (from Top) to PDF Point Y (from Bottom)"""
        # Scale Y
        scaled_y = px * (PAGE_HEIGHT / self.IMG_HEIGHT)
        # Invert axis
        return PAGE_HEIGHT - scaled_y

    def generate(self, segments, daily_logs, user_info, output_path, debug=False):
        c = canvas.Canvas(output_path, pagesize=A4)
        
        # 1. Draw Template Background
        if os.path.exists(self.template_path):
            c.drawImage(self.template_path, 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        else:
            c.drawString(100, 500, "Template not found at assets/template.png")
            
        # 2. Draw Header
        if user_info:
            self._draw_header(c, user_info)
            
        # 3. Draw Data
        self._draw_data(c, segments)
        
        # 4. Draw Daily Metrics (Sleepiness, Notes) & Events
        self._draw_daily_metrics_and_events(c, daily_logs)
        
        # 5. Draw Debug Grid (Pixels)
        if debug:
            self._draw_pixel_grid(c)
            
        c.save()
        
    def _draw_header(self, c, info):
        # Font size reduced (14 -> 8)
        c.setFont("HeiseiKakuGo-W5", 8) 
        
        y_pdf = self._px_to_pdf_y(self.HEADER_Y_PX)
        
        # ID
        x = self._px_to_pdf_x(self.HEADER_ID_X)
        c.drawString(x, y_pdf, str(info.get('id', '')))
        
        # Name
        x = self._px_to_pdf_x(self.HEADER_NAME_X)
        c.drawString(x, y_pdf, str(info.get('name', '')))
        
        # Year (Show only last 2 digits)
        x = self._px_to_pdf_x(self.HEADER_YEAR_X)
        year_str = str(info.get('year', ''))
        if len(year_str) == 4:
            year_str = year_str[-2:] 
        c.drawString(x, y_pdf, year_str)
        
        # Month
        x = self._px_to_pdf_x(self.HEADER_MONTH_X)
        c.drawString(x, y_pdf, str(info.get('month', '')))
        
    def _draw_daily_metrics_and_events(self, c, daily_logs):
        if not daily_logs:
            return
            
        import textwrap
        
        for day_index, log in daily_logs.items():
            if day_index < 0 or day_index > 30: continue
            
            # Y Base from List
            if day_index >= len(self.DAILY_Y_STARTS): continue
            y_top_px = self.DAILY_Y_STARTS[day_index]
            
            # --- Sleepiness ---
            if log.get('sleepiness'):
                c.setFont("HeiseiKakuGo-W5", 10) # Standard
                c.setFillColor(black)
                sx = self._px_to_pdf_x(self.X_SLEEPINESS_START)
                sy = self._px_to_pdf_y(y_top_px + 40) 
                c.drawString(sx, sy, str(log['sleepiness']))
            
            # --- Memo (Small font + Wrap) ---
            if log.get('memo'):
                c.setFont("HeiseiKakuGo-W5", 6) # Small font
                mx = self._px_to_pdf_x(self.X_NOTE_START)
                my_base = self._px_to_pdf_y(y_top_px + 15) # Start higher
                
                # Wrap text (approx 20 chars per line - adjusted for single line sleep time)
                lines = textwrap.wrap(log['memo'], width=20)
                
                for i, line in enumerate(lines[:3]): # Max 3 lines
                    c.drawString(mx, my_base - (i * 7), line)

            # --- Total Sleep Time (Separate Line) ---
            if log.get('total_sleep'):
                 c.setFont("HeiseiKakuGo-W5", 6)
                 tx = self._px_to_pdf_x(self.X_NOTE_START)
                 # Position near bottom of the row (Height ~64px)
                 ty = self._px_to_pdf_y(y_top_px + 55) 
                 c.drawString(tx, ty, str(log['total_sleep']))
                
            # --- Events ---
            events = log.get('events', [])
            c.setFont("HeiseiKakuGo-W5", 10) # Restore
            for evt in events:
                # Logic same as _draw_data for X
                total_hours = self.TIME_END_NOTATION - self.TIME_START_NOTATION
                x_width_px = self.X_TIME_END_PX - self.X_TIME_START_PX
                
                offset = evt['time'] - self.TIME_START_NOTATION
                px_x = self.X_TIME_START_PX + (x_width_px * (offset / total_hours))
                pdf_x = self._px_to_pdf_x(px_x)
                
                # Y position - moved to In-bed row (lower half)
                # In-bed arrow line is at y_top_px + 45. Align markers there.
                pdf_y = self._px_to_pdf_y(y_top_px + 45)
                
                # Symbol
                symbol = "●"
                t_type = evt.get('type', '')
                if "sleep_med" in t_type: symbol = "▲"
                elif "toilet" in t_type: symbol = "▽"
                
                c.drawString(pdf_x - 3, pdf_y, symbol)

    def _draw_data(self, c, data):
        """Draw sleep data bars from actual data"""
        # data is expected to be a list of dictionaries:
        # { 'day_index': int (0-30), 'start_hour': float, 'end_hour': float, 'type': str }
        
        if not data:
            return

        for segment in data:
            day_index = segment['day_index']
            # Safety check
            if day_index < 0 or day_index > 30:
                continue

            # --- Y Coordinate Calculation from List ---
            if day_index >= len(self.DAILY_Y_STARTS): continue
            y_top_px = self.DAILY_Y_STARTS[day_index]
            
            # --- X Coordinate Calculation ---
            total_hours = self.TIME_END_NOTATION - self.TIME_START_NOTATION
            x_width_px = self.X_TIME_END_PX - self.X_TIME_START_PX
            
            # Helper to calculate pixel X from hour
            def get_px_x(h):
                # Normalize overlaps (e.g. 25:00 -> 25.0)
                offset = h - self.TIME_START_NOTATION
                return self.X_TIME_START_PX + (x_width_px * (offset / total_hours))

            start_hour = segment['start_hour']
            end_hour = segment['end_hour']
            
            x_start_px = get_px_x(start_hour)
            x_end_px = get_px_x(end_hour)
            
            pdf_x_start = self._px_to_pdf_x(x_start_px)
            pdf_x_end = self._px_to_pdf_x(x_end_px)
            pdf_w = pdf_x_end - pdf_x_start
            
            # Set Color based on type
            s_type = segment.get('type', 'In-bed')
            
            # --- Draw Logic ---
            if 'In-bed' in s_type:
                # LOWER HALF: Arrow Line
                # Y position for the arrow line (approx 45px from top, in the lower frame)
                arrow_y_offset = 45 
                y_arrow_px = y_top_px + arrow_y_offset
                pdf_y_arrow = self._px_to_pdf_y(y_arrow_px)
                
                c.setStrokeColor(blue)
                c.setLineWidth(1.5)
                c.line(pdf_x_start, pdf_y_arrow, pdf_x_end, pdf_y_arrow)
                
                # Draw Arrowheads (manual)
                arrow_size = 3
                # Left Arrow (<)
                p = c.beginPath()
                p.moveTo(pdf_x_start + arrow_size, pdf_y_arrow + arrow_size)
                p.lineTo(pdf_x_start, pdf_y_arrow)
                p.lineTo(pdf_x_start + arrow_size, pdf_y_arrow - arrow_size)
                c.drawPath(p, stroke=1, fill=0)
                
                # Right Arrow (>)
                p = c.beginPath()
                p.moveTo(pdf_x_end - arrow_size, pdf_y_arrow + arrow_size)
                p.lineTo(pdf_x_end, pdf_y_arrow)
                p.lineTo(pdf_x_end - arrow_size, pdf_y_arrow - arrow_size)
                c.drawPath(p, stroke=1, fill=0)
                
            else:
                # UPPER HALF: Texture/Shape Representation
                # Y position (offset 4px from top)
                bar_height_px = 18
                y_offset_px = 4
                y_bar_top_px = y_top_px + y_offset_px
                img_bar_bottom_px = y_bar_top_px + bar_height_px
                
                pdf_y_bottom = self._px_to_pdf_y(img_bar_bottom_px)
                pdf_y_top = self._px_to_pdf_y(y_bar_top_px)
                pdf_h = pdf_y_top - pdf_y_bottom
                
                # Unified Color: Blue
                c.setStrokeColor(blue)
                c.setFillColor(blue)
                c.setLineWidth(0.5)
                
                if 'Deep' in s_type:
                    # 1. ぐっすり -> 塗りつぶし (Solid Fill)
                    c.rect(pdf_x_start, pdf_y_bottom, pdf_w, pdf_h, stroke=0, fill=1)
                    
                elif 'Doze' in s_type:
                    # 2. うとうと -> 斜線 (Diagonal Hatching)
                    # Draw border first
                    c.rect(pdf_x_start, pdf_y_bottom, pdf_w, pdf_h, stroke=1, fill=0)
                    
                    # Create clipping region for lines
                    c.saveState()
                    p = c.beginPath()
                    p.rect(pdf_x_start, pdf_y_bottom, pdf_w, pdf_h)
                    c.clipPath(p, stroke=0, fill=0)
                    
                    # Draw diagonal lines
                    # Simple 45 degree lines: (x, bottom) -> (x+h, top)
                    step = 3 # density of hatching
                    # Start X needs to be shifted left by height to cover the left triangle corner
                    start_draw_x = int(pdf_x_start - pdf_h)
                    end_draw_x = int(pdf_x_end)
                    
                    for x in range(start_draw_x, end_draw_x, step):
                        c.line(x, pdf_y_bottom, x + pdf_h, pdf_y_top)
                        
                    c.restoreState()
                    
                elif 'Awake' in s_type:
                    # 3. 眠れない -> 枠線のみ (Frame only)
                    c.setLineWidth(1.0)
                    c.rect(pdf_x_start, pdf_y_bottom, pdf_w, pdf_h, stroke=1, fill=0)
                else:
                    # Fallback -> Solid 
                    c.rect(pdf_x_start, pdf_y_bottom, pdf_w, pdf_h, stroke=0, fill=1)

    def _draw_pixel_grid(self, c):
        """Draw grid based on Image Pixels"""
        c.setStrokeColor(red)
        c.setLineWidth(0.5)
        c.setFont("Helvetica", 6)
        c.setFillColor(red)
        
        # Vertical Lines (X) every 100px
        for x_px in range(0, self.IMG_WIDTH, 100):
            p_x = self._px_to_pdf_x(x_px)
            c.line(p_x, 0, p_x, PAGE_HEIGHT)
            c.drawString(p_x + 1, PAGE_HEIGHT - 10, str(x_px))
            
        # Horizontal Lines (Y) every 100px
        for y_px in range(0, self.IMG_HEIGHT, 100):
            p_y = self._px_to_pdf_y(y_px)
            c.line(0, p_y, PAGE_WIDTH, p_y)
            c.drawString(1, p_y + 1, str(y_px))
            
        # Highlight Layout Constants (Daily Rows)
        c.setStrokeColor(blue)
        c.setLineWidth(0.5)
        
        # Draw line for each day start
        for i, y_start in enumerate(self.DAILY_Y_STARTS):
             y = self._px_to_pdf_y(y_start)
             c.line(0, y, PAGE_WIDTH, y)
             # Label every 5 days to avoid clutter
             if (i+1) % 5 == 1:
                c.drawString(50, y+2, f"D{i+1}: {y_start}")
        
        # X Start
        x = self._px_to_pdf_x(self.X_TIME_START_PX)
        c.line(x, 0, x, PAGE_HEIGHT)
        c.drawString(x+2, 400, f"Start (X={self.X_TIME_START_PX})")
        
        # X End
        x = self._px_to_pdf_x(self.X_TIME_END_PX)
        c.line(x, 0, x, PAGE_HEIGHT)
        c.drawString(x+2, 400, f"End (X={self.X_TIME_END_PX})")

if __name__ == "__main__":
    gen = SleepPDFGenerator()
    gen.generate({}, "test_output.pdf", debug=True)
