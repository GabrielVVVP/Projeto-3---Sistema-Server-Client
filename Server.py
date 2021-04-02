from enlace import *
import time
import numpy as np

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
# para saber a sua porta, execute no terminal :
# python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

#use uma das 3 opcoes para atribuir à variável a porta usada
#serialName = "/dev/ttyACM0"           # Ubuntu (variacao de)
#serialName = "/dev/tty.usbmodem1411" # Mac    (variacao de)

class Server:
    
    def __init__(self, img_location, TX, RX, baudrate):
        self.location_w  = img_location
        self.comTX       = TX
        self.comRX       = RX
        self.rxBuffer_H = 0
        self.rxBuffer = 0
        self.rxBuffer_resp = 0
        self.count = 1
        self.arquivo_recebido = bytearray()
        self.Baud_Rate = baudrate
    
    def handshake_analyzer(self,buffer):
        self.num_value = int.from_bytes(buffer[:4], byteorder="big")
        self.size_value = int.from_bytes(buffer[4:10], byteorder="big")
        end_value = int.from_bytes(buffer[-4:], byteorder="big")
        
        if end_value==404:
            respost = "O Handshake do Client foi recebido corretamente."
            return respost 
        else:
            errormsg = "O Handshake do Client não foi recebido corretamente."   
            return errormsg
    
    def package_analyzer(self,buffer, quantity, id_num, size):
        id_value = int.from_bytes(buffer[:4], byteorder="big")
        quantity_value = int.from_bytes(buffer[4:9], byteorder="big") 
        read_pkg = buffer[9]
        end_value = int.from_bytes(buffer[-4:], byteorder="big")       
        full_payload = buffer[10:-4]
            
        if (id_value == id_num+1)and(quantity_value==quantity)and(len(full_payload)==114)and(end_value==404):
            respost = "Tudo correto."
            return respost, read_pkg 
        else:
            errormsg = "Ocorreu(eram) os seguinte(s) erros: "
            if (id_value != id_num+1):
                errormsg += "ID incorreto no Head. "
            elif (quantity_value!=quantity):
                errormsg += "Quantidade total de pacotes incorreta no Head. "
            elif (len(full_payload)!=114):
                errormsg += "Tamanho do Payload incorreto. "
            elif (end_value!=404):
                errormsg += "Valor final incorreto."    
            return errormsg, read_pkg    
        
    def init_comm(self):
            try:
                print("-------------------------")
                print("Server Started")
                print("-------------------------")
                
                # Declaramos um objeto do tipo enlace com o nome "com". Essa é a camada inferior à aplicação. Observe que um parametro
                # para declarar esse objeto é o nome da porta.
                self.STX = enlace(self.comTX, self.Baud_Rate)
                self.SRX = enlace(self.comRX, self.Baud_Rate)
                
                # Ativa comunicacao. Inicia os threads e a comunicação serial 
                self.STX.enable()
                self.SRX.enable()
                self.count = 1
                
                # Se chegamos até aqui, a comunicação foi aberta com sucesso. Faça um print para informar.
                server_init_msg1 = "Server TX iniciado na porta: {}.".format(self.comTX)
                server_init_msg2 = "Server RX iniciado na porta: {}.".format(self.comRX)
                
                print(server_init_msg1)
                print(server_init_msg2) 
                print("-------------------------")
                
                # Local da imagem a ser salva
                server_init_msg3 = "Local onde a imagem recebida será salva: {}.".format(self.location_w)
                print(server_init_msg3)
                print("-------------------------")
                
                # Espera os dados do Header - Client
                server_init_msg4 = "Esperando o Handshake do Client."
                print(server_init_msg4)
                time.sleep(1)
                
                return([server_init_msg1,server_init_msg2,server_init_msg3,server_init_msg4])
            
            except Exception as erro:
                print("ops! :-\\")
                print(erro)
                self.STX.disable()
                self.SRX.disable()  
                
    def handshake_receive_response(self):
            try:
                self.rxBuffer_H, nRx_H = self.SRX.getData(14,use_timeout=1)
                server_comm_msg = self.handshake_analyzer(self.rxBuffer_H)
                print(server_comm_msg)
                print("-------------------------")
                
                return([server_comm_msg,self.num_value])
            
            except Exception as erro:
                print("ops! :-\\")
                print(erro)
                self.STX.disable()
                self.SRX.disable() 
                
    def execution_start(self):
        try:
            # Retornando uma resposta do Header para o Client
            server_time_msg = "Enviando uma resposta do Handshake para o Client."
            print(server_time_msg)
            self.STX.sendData(np.asarray(self.rxBuffer_H))
            print("-------------------------")
            
            # Começar o cronometro do tempo de execução do envio
            server_time_msg2 = "Recebendo os pacotes do Client."
            print(server_time_msg2)
            print("-------------------------")
            
            return([server_time_msg,server_time_msg2])
            
        except Exception as erro:
            print("ops! :-\\")
            print(erro)
            self.CTX.disable()
            self.CRX.disable()             
                
    def data_receive_response(self, count):
            try:  
                self.rxBuffer, nRx = self.SRX.getData(128)    
                package_check, read_pack = self.package_analyzer(self.rxBuffer, self.num_value, count-1, self.size_value)
                if (package_check=="Tudo correto."):
                    server_data_msg1 = "Pacote recebido corretamente."
                    print(server_data_msg1)
                    server_data_msg2 = "Pacote atual: {} de {}.".format(count,self.num_value)
                    print(server_data_msg2)
                    count+=1
                    self.arquivo_recebido+=self.rxBuffer[10:10+read_pack]
                else:
                    server_data_msg1 = package_check
                    print(server_data_msg1)
                    server_data_msg2 = "Pacote atual: {} de {}.".format(count,self.num_value)
                    print(server_data_msg2)
                print("-------------------------")    
                self.STX.sendData(np.asarray(self.rxBuffer)) 
                
                return([server_data_msg1,server_data_msg2, count])
            
            except Exception as erro:
                print("ops! :-\\")
                print(erro)
                self.STX.disable()
                self.SRX.disable()
    
    def execution_end(self):
        try:
            # Acesso aos bytes recebidos
            client_ex_msg1 = "Enviando a resposta de conclusão da conexão."
            print(client_ex_msg1)
            self.STX.sendData(np.asarray(self.rxBuffer_H))
            time.sleep(1)
            
            return([client_ex_msg1])
            
        except Exception as erro:
            print("ops! :-\\")
            print(erro)
            self.CTX.disable()
            self.CRX.disable()             
                
    def end_connection(self):
            try:
                # Salva imagem
                print("-------------------------")
                image_name = self.location_w.split("\\")
                server_end_msg1 = "Salvando dados no arquivo: {}.".format(image_name[1])
                print(server_end_msg1)
                f = open(self.location_w, "wb")
                f.write(self.arquivo_recebido)
            
                # Encerra comunicação
                print("-------------------------")
                server_end_msg2 = "Comunicação encerrada com as portas {} e {}.".format(self.comTX,self.comRX)
                print(server_end_msg2)
                print("-------------------------")
                self.STX.disable()
                self.SRX.disable() 
                
                return([server_end_msg1,server_end_msg2])
            
            except Exception as erro:
                print("ops! :-\\")
                print(erro)
                self.STX.disable()
                self.SRX.disable()                   