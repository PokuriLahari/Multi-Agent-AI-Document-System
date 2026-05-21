import html
import re

def render_output(output):
    escaped_out = html.escape(str(output))
    escaped_out = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #ffffff;">\1</strong>', escaped_out)
    escaped_out = re.sub(r'^### (.*?)$', r'<div style="font-size:16px; font-weight:bold; color:#a78bfa; margin-top:12px; margin-bottom:6px;">\1</div>', escaped_out, flags=re.MULTILINE)
    escaped_out = re.sub(r'^## (.*?)$', r'<div style="font-size:18px; font-weight:bold; color:#a78bfa; margin-top:14px; margin-bottom:8px;">\1</div>', escaped_out, flags=re.MULTILINE)
    escaped_out = re.sub(r'^# (.*?)$', r'<div style="font-size:20px; font-weight:bold; color:#c4b5fd; margin-top:16px; margin-bottom:10px;">\1</div>', escaped_out, flags=re.MULTILINE)
    escaped_out = re.sub(r'^- (.*?)$', r'<li style="margin-left: 16px;">\1</li>', escaped_out, flags=re.MULTILINE)
    escaped_out = re.sub(r'^\* (.*?)$', r'<li style="margin-left: 16px;">\1</li>', escaped_out, flags=re.MULTILINE)
    escaped_out = escaped_out.replace('\n', '<br>')
    return escaped_out

print(render_output("Hello\n**world**\n### Header"))
