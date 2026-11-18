#id mc_rest_api_simple_GET_example.py 2026-11-18
# MovingCap CODE - simple REST-API server on Port 8080
# supports Object Read (OR) requests via HTTP GET.
# Example: Client requests from MovingCap object 3401h.0ah temperature value:
# http://192.168.2.152:8080/OR/0x3401/0x0a
# MovingCap REST server answer:
# {"status": "success", "index": "0x3401", "subindex": 10, "value": 35}

import mcnet
import mcdrive as mc
import time

def parse_int(s):
    """Hilfsfunktion zum Parsen von Dezimal- und Hexadezimalwerten"""
    s = s.strip()
    if s.startswith("0x") or s.startswith("0X"):
        return int(s, 16)
    elif s.endswith("h") or s.endswith("H"):
        return int(s.rstrip("hH"), 16)
    else:
        return int(s)

def main():
    print("Starte REST-API Server auf Port 8080...")
    
    # TCP-Server auf Port 8080 initialisieren
    server = mcnet.McNet("SERVER:8080")
    
    # Zeilenmodus konfigurieren: Textmodus, kein Start-Marker, Newline als End-Marker
    server.set_line_mode(1, 0, ord('\n'), 0, 0, 5000)
    
    while True:
        # Prüfen, ob ein Client verbunden ist
        if server.is_connected():
            # Erste Zeile des HTTP-Requests lesen (z.B. "GET /OR/0x6064/0 HTTP/1.1")
            request_line = server.readline()
            
            if request_line:
                print("Anfrage empfangen:", request_line.strip())
                
                # Restliche HTTP-Header einlesen und verwerfen (bis zur Leerzeile)
                while True:
                    header = server.readline()
                    if not header or header == "\r\n" or header == "\n":
                        break
                
                status_code = "200 OK"
                response_body = ""
                
                try:
                    # Request-Zeile parsen (z.B. ["GET", "/OR/0x6064/0", "HTTP/1.1"])
                    parts = request_line.split(" ")
                    if len(parts) >= 2:
                        method = parts[0]
                        path = parts[1]
                        
                        if method == "GET":
                            index = None
                            subindex = 0
                            
                            # Format 1: /OR/index/subindex
                            if path.startswith("/OR/"):
                                path_parts = path.split("/")
                                if len(path_parts) >= 4:
                                    index = parse_int(path_parts[2])
                                    subindex = parse_int(path_parts[3])
                            
                            # Format 2: /ORindex,subindex
                            elif path.startswith("/OR"):
                                cmd_str = path.split("/OR")[1]
                                path_parts = cmd_str.split(",")
                                if len(path_parts) >= 2:
                                    index = parse_int(path_parts[0])
                                    subindex = parse_int(path_parts[1])
                            
                            if index is not None:
                                # CANopen-Objekt auslesen
                                value = mc.ReadObject(index, subindex)
                                
                                # JSON-Antwort erstellen (ohne f-Strings)
                                response_body = '{"status": "success", "index": "0x%04X", "subindex": %d, "value": %d}' % (index, subindex, value)
                            else:
                                status_code = "400 Bad Request"
                                response_body = '{"status": "error", "message": "Ungueltiges Format. Nutzen Sie /OR/index/subindex oder /ORindex,subindex"}'
                        else:
                            status_code = "405 Method Not Allowed"
                            response_body = '{"status": "error", "message": "Nur GET-Methode erlaubt"}'
                    else:
                        status_code = "400 Bad Request"
                        response_body = '{"status": "error", "message": "Ungueltige HTTP-Anfrage"}'
                        
                except Exception as e:
                    status_code = "500 Internal Server Error"
                    response_body = '{"status": "error", "message": "Fehler beim Verarbeiten der Anfrage"}'
                
                # HTTP-Antwort senden
                response = "HTTP/1.1 " + status_code + "\r\n"
                response += "Content-Type: application/json\r\n"
                response += "Content-Length: " + str(len(response_body)) + "\r\n"
                response += "Connection: close\r\n"
                response += "\r\n"
                response += response_body
                
                server.write(response)
                
                # Kurze Pause, um den Sendevorgang abzuschließen
                time.sleep_ms(100)
                
                # Verbindung trennen und Server für den nächsten Client zurücksetzen
                server.close()
                server.open("SERVER:8080")
                server.set_line_mode(1, 0, ord('\n'), 0, 0, 5000)
                
        # CPU-Last minimieren
        time.sleep_ms(10)

if __name__ == "__main__":
    main()
