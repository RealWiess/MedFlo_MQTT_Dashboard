import os
import sys
import socket
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8080

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

class MedFlowHTTPHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.path = '/mqtt_dashboard.html'
        return super().do_GET()

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    local_ip = get_local_ip()
    url = f"http://{local_ip}:{PORT}/mqtt_dashboard.html"
    
    print("=" * 65)
    print("🏥 MedFlow 滴護寶藍芽動態監測牆 - 全平台一鍵開啟服務已啟動")
    print("=" * 65)
    print(f"💻 本機電腦 (Windows / Mac) 雙擊即開:  http://localhost:{PORT}")
    print(f"📱 移動裝置 (Android / iPhone / iPad) 掃碼連線:")
    print(f"👉 網址: 【 {url} 】")
    print("-" * 65)
    print("✨ 一鍵體驗指引:")
    print("  1. Windows / Mac 用戶: 系統已自動幫您開啟瀏覽器視窗！")
    print("  2. 手機 / 平板用戶: 拿起相機掃描電腦畫面上的 QR Code 即可一鍵載入。")
    print("=" * 65)

    try:
        webbrowser.open(f"http://localhost:{PORT}")
    except Exception:
        pass

    httpd = HTTPServer(('0.0.0.0', PORT), MedFlowHTTPHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n伺服器已停止。")
        sys.exit(0)

if __name__ == '__main__':
    main()
