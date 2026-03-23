#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json
import subprocess
import threading

BASE_DIR = Path(__file__).parent
INDEX = BASE_DIR / "static" / "index.html"

# ---- IMPORTANT: keep commands allowlisted and argument-array based (no shell=True). [1](https://rowdendefence-my.sharepoint.com/personal/johnmurray_rowdentech_com/_layouts/15/Doc.aspx?sourcedoc=%7B66857FBF-00DA-4DBD-9FC6-4A0804045FAB%7D&file=basic%20UI%20for%20sdr%20tool.docx&action=default&mobileredirect=true)
# We'll start with placeholders that echo what would happen, then you can swap in systemctl/welle/rtl_fm commands.

STOP_ALL = ["bash", "-lc", "echo 'STOP_ALL placeholder (replace with systemctl stop ...)'"]

ALLOWED = {
	# Utility
	"stop_all_sdr": STOP_ALL,

	# DAB (placeholders for now)
	"dab_leeds_11b": ["bash", "-lc", "echo 'DAB Leeds 11B placeholder (replace with wellle-cli / systemd oneshot)'"],
	"dab_5lse":  	["bash", "-lc", "echo 'DAB 5 Live Sports Extra placeholder (replace with wellle-cli / systemd oneshot)'"],

	# FM (placeholder for now)
	"fm_leeds":  	["bash", "-lc", "echo 'FM Leeds placeholder (replace with rtl_fm / systemd service)'"],

	# SDR++ server control (placeholder for now)
	"sdrpp_server_start":  ["bash", "-lc", "echo 'SDR++ server start placeholder (replace with systemctl start sdrpp-server)'"],
	"sdrpp_server_stop":   ["bash", "-lc", "echo 'SDR++ server stop placeholder (replace with systemctl stop sdrpp-server)'"],
	"sdrpp_server_status": ["bash", "-lc", "echo 'SDR++ server status placeholder (replace with systemctl status sdrpp-server --no-pager)'"],
}

LOCK = threading.Lock()


def run_cmd(cmd):
	"""Run a command safely (no shell=True). Return combined stdout/stderr."""
	try:
		out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
		return out.decode(errors="replace")
	except subprocess.CalledProcessError as e:
		return e.output.decode(errors="replace")


class Handler(BaseHTTPRequestHandler):
	def do_GET(self):
		if self.path in ("/", "/index.html"):
			if not INDEX.exists():
				self.send_error(404, "static/index.html not found")
				return
			body = INDEX.read_bytes()
			self.send_response(200)
			self.send_header("Content-Type", "text/html; charset=utf-8")
			self.send_header("Content-Length", str(len(body)))
			self.end_headers()
			self.wfile.write(body)
			return
		self.send_error(404)

	def do_POST(self):
		if self.path != "/run":
			self.send_error(404)
			return
		length = int(self.headers.get("Content-Length", "0"))
		raw = self.rfile.read(length)
		try:
			data = json.loads(raw.decode("utf-8"))
		except json.JSONDecodeError:
			self.send_error(400, "Bad JSON")
			return
		action = data.get("action")
		if action == "sdrpp_gui_help":
        	# SDR++ GUI is "different": we return instructions rather than trying to spawn a GUI from a web handler.
			msg = (
            	"SDR++ GUI help:\n"
            	"1) Preferred: run SDR++ GUI on your laptop and connect to the Pi's SDR++ server.\n"
            	"2) Alternative (X11 forwarding): ssh -Y <pi_user>@<pi_ip> sdrpp\n"
        	)
			self._ok(msg)
			return
		if action not in ALLOWED:
			self.send_error(400, "Invalid action")
			return

    	# Enforce 'stop before start' for SDR ownership where appropriate
		if action.startswith(("dab_", "fm_", "sdrpp_server_start")):
			out_lines.append("Stopping all SDR users first...")
			out_lines.append(run_cmd(STOP_ALL))
			out_lines.append(f"Running action: {action}")
			out_lines.append(run_cmd(ALLOWED[action]))
			self._ok("\n".join(out_lines))

	def _ok(self, text):
		self.send_response(200)
		self.send_header("Content-Type", "text/plain; charset=utf-8")
		self.end_headers()
		self.wfile.write(text.encode("utf-8"))

	def log_message(self, format, *args):
    	# Keep logs quiet; comment this out if you want request logs.
		return


def main():
	server = HTTPServer(("0.0.0.0", 8080), Handler)
	print("SDR UI server running on http://0.0.0.0:8080")
	server.serve_forever()

if __name__ == "__main__":
	main()