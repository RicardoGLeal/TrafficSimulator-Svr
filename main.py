"""
    Script to create a server which calls the model.step from
    an MAS implementation

    From unity side, you can watch this video:
    https://www.youtube.com/watch?v=GIxu8kA9EBU

"""


# Install pyngrok to propagate the http server
# pip install pyngrok 

# Load the required packages
from pyngrok        import ngrok
from http.server    import BaseHTTPRequestHandler, HTTPServer

import json
import logging
import os
import pandas as pd

# Import MAS module
from trafficSimulator import TrafficSimulator

# Invoke model
mapa = pd.read_csv("grafo.csv", header= None).values
semaphore_ticks = 15
new_model = TrafficSimulator(*mapa.shape, number_of_agents = 15, ticks = semaphore_ticks)
data = new_model.datacollector.get_model_vars_dataframe()

#print(data.to_string())


# Commented out IPython magic to ensure Python compatibility.
# %%capture
# fig, axs = plt.subplots(figsize=(7,7))
# patch = plt.imshow(data.iloc[0][0], cmap=plt.cm.binary)

# def animate(index):
#   patch.set_data(data.iloc[index][0])

# anim = animation.FuncAnimation(fig, animate, frames=Iterations)
# from IPython.display import HTML
# HTML(anim.to_jshtml())
# while((time.time() - start_time) < tiempo_maximo and not model.todoLimpio()):

def getFeaturesVehiculos(data):
    features = []
    for elem in data:
        # import pdb; pdb.set_trace()
        feature = {'carroID' : elem['carroID'], 'wayPointID' : elem['wayPointID']}
        #feature2 = {'semaforoEncendido' : elem['semaforoEncendido']}
        features.append(feature)
        #features.append(feature2)

    return json.dumps(features)

class Server(BaseHTTPRequestHandler):
    
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", 
                     str(self.path), str(self.headers))
        self._set_response()

        new_model.step()
        vehiculosData = new_model.status_agentes()

        # obtener los datos del modelo...
        resp = "{\"data\":" + "{\"vehiculos\":" + getFeaturesVehiculos(vehiculosData) + "}," + "\"semaforos\":" + str(new_model.get_status_lights()) + "}"
        self.wfile.write(resp.encode('utf-8'))

    def do_POST(self):
        pass

def run(server_class=HTTPServer, handler_class=Server, port=8585):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)

    public_url = ngrok.connect(port).public_url
    logging.info(f"ngrok tunnel \"{public_url}\" -> \"http://127.0.0.1:{port}\"")

    logging.info("Starting httpd...\n") # HTTPD is HTTP Daemon!
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:   # CTRL + C stops the server
        pass

    httpd.server_close()
    logging.info("Stopping httpd...\n")


if __name__ == "__main__":
    # server
    run(HTTPServer, Server)
    
    
    
    
