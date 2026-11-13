"""Editorial layout for the Gemini support-routing edition."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PAPER, INK, BLUE = '#f6f3ea', '#171e2a', '#163ceb'
SOFT, MUTED = '#e0e7ff', '#4c5665'
FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')


def render_gemini(item, directory):
    directory.mkdir(parents=True, exist_ok=True)
    for page in range(1, 5):
        image = Image.new('RGB', (1080, 1350), PAPER)
        draw = ImageDraw.Draw(image)

        def text(x, y, words, size, color=INK, face='Sans', anchor='la', leading=12):
            font = ImageFont.truetype(str(FONT_DIR / f'DejaVu{face}.ttf'), size)
            draw.multiline_text((x, y), words, font=font, fill=color, anchor=anchor, spacing=leading)

        def line(points, color=INK, width=2):
            draw.line(points, fill=color, width=width)

        def box(bounds, color):
            draw.rectangle(bounds, fill=color)

        text(72, 55, 'The Technology Brief', 48, face='Serif-Bold')
        text(1008, 71, '13 NOV 2026', 23, MUTED, anchor='ra')
        line((72, 137, 1008, 137))
        text(72, 170, 'ENTERPRISE AI', 26, BLUE, 'Sans-Bold')

        if page == 1:
            text(66, 239, 'One input. Up to\n1,000 AI checks.', 91, face='Serif-Bold', leading=4)
            text(73, 482, 'Google’s Gemini Decisions API,\nexplained with one support ticket.', 38, MUTED)
            box((72, 635, 1008, 1158), BLUE)
            box((122, 735, 421, 1025), '#ffffff')
            text(151, 777, 'SUPPORT TICKET', 25, BLUE, 'Sans-Bold')
            for y, length in [(854, 197), (892, 224), (930, 148)]:
                box((151, y, 151 + length, y+10), SOFT)
            line((421, 880, 543, 880), '#ffffff', 4)
            line((543, 740, 543, 1020), '#ffffff', 4)
            for y, word in [(740, 'Route'), (880, 'Flag'), (1020, 'Review')]:
                line((543, y, 630, y), '#ffffff', 4)
                box((630, y-48, 958, y+48), SOFT)
                text(666, y-26, word, 43, INK, 'Sans-Bold')
        elif page == 2:
            text(69, 242, 'Start with one\nsupport ticket.', 86, face='Serif-Bold', leading=3)
            box((72, 485, 1008, 714), SOFT)
            text(110, 515, 'EXAMPLE TICKET', 23, BLUE, 'Sans-Bold')
            text(110, 574, '“I was charged twice\nfor the same invoice.”', 43, face='Serif')
            text(72, 790, 'Ask about the same input:', 35, face='Sans-Bold')
            for y, question in [(882, 'Is this a billing issue?'), (975, 'Is a duplicate charge reported?'),
                                (1068, 'Which team should handle it?')]:
                line((72, y-16, 1008, y-16), '#9aabd5')
                text(72, y, question, 37)
        elif page == 3:
            text(69, 241, 'From answers\nto a routing rule.', 80, face='Serif-Bold', leading=3)
            text(72, 460, 'Illustrative result for the example ticket', 32, MUTED)
            for y, title, answer in [(567, 'Billing issue', 'Yes'), (686, 'Duplicate charge', 'Reported'),
                                     (805, 'Suggested queue', 'Billing support')]:
                line((72, y, 1008, y), '#9aabd5')
                text(72, y+32, title, 37)
                text(1008, y+32, answer, 37, BLUE, 'Sans-Bold', anchor='ra')
            box((72, 965, 1008, 1157), BLUE)
            text(104, 1005, 'Pilot rule', 29, '#ffffff', 'Sans-Bold')
            text(104, 1058, 'Send uncertain or conflicting results\nto a human reviewer.', 33, '#ffffff')
        else:
            text(69, 242, 'Before you automate\nticket routing.', 74, face='Serif-Bold', leading=3)
            for n, (title, desc) in enumerate([
                ('Start with labeled tickets', 'Use past cases with an agreed correct queue.'),
                ('Measure wrong routes', 'Compare against your current process.\nRecord time and cost per ticket.'),
                ('Keep a human fallback', 'Test your confidence threshold on labeled\ncases before you enable auto-routing.'),
            ]):
                y = 519 + 210*n
                line((72, y-14, 1008, y-14), '#9aabd5')
                text(72, y+9, f'{n+1:02}', 38, BLUE, 'Serif-Bold')
                text(169, y+8, title, 39, face='Sans-Bold')
                text(171, y+74, desc, 31, MUTED)

        line((72, 1212, 1008, 1212))
        text(72, 1242, 'Source  •  Google DeepMind, 11 Nov 2026', 24, MUTED)
        text(1008, 1242, f'{page} / 4', 24, BLUE, 'Sans-Bold', anchor='ra')
        image.save(directory / f"{item['id']}-{page}.jpg", quality=94, subsampling=0)
