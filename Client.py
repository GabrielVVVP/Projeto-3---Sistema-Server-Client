from enlace import *
import time
import numpy as np
import random

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

#use uma das 3 opcoes para atribuir à variável a porta usada
#serialName = "/dev/ttyACM0"           # Ubuntu (variacao de)
#serialName = "/dev/tty.usbmodem1411" # Mac    (variacao de)

class Client:
    
    def __init__(self, img_location, TX, RX, baudrate):
        self.location_r  = img_location
        self.comTX       = TX
        self.comRX       = RX
        self.txBuffer = 0
        self.txBuffer_len = 0
        self.rxBuffer_H = 0
        self.rxBuffer_D = 0
        self.count = 1
        self.numberofpackages = 0
        self.start_time = 0
        self.execution_time = 0
        self.Baud_Rate = baudrate
    
    def package_analyzer(self,buffer, quantity, id_num, size):
        id_value = int.from_bytes(buffer[:4], byteorder="big")
        quantity_value = int.from_bytes(buffer[4:9], byteorder="big")
        end_value = int.from_bytes(buffer[-4:], byteorder="big") 
        wrong_value = buffer[-5]
            
        if (id_value == id_num+1)and(quantity_value==quantity)and(wrong_value!=203)and(end_value==404):
            respost = "Tudo correto."
            return respost 
        else:
            errormsg = "Ocorreu(eram) os seguinte(s) erros: "
            if (id_value != id_num+1):
                errormsg += "ID incorreto no Head. "
            elif (quantity_value!=quantity):
                errormsg += "Quantidade total de pacotes incorreta no Head. "
            elif (wrong_value==203):
                errormsg += "Tamanho do Payload incorreto. "
            elif (end_value!=404):
                errormsg += "Valor final incorreto."    
            return errormsg
        
    def package_errors(self,buffer,force_errors=0):
        # Force Errors
        if(force_errors==1):
            id_value = int.from_bytes(buffer[:4], byteorder="big")
            id_value+=1
            id_val = (id_value).to_bytes(4, byteorder="big")
            buffer = id_val+buffer[4:]
        elif(force_errors==2):
            quantity_value = int.from_bytes(buffer[4:9], byteorder="big")
            quantity_value+=1
            q_val = (quantity_value).to_bytes(4, byteorder="big")
            buffer = buffer[:4]+q_val+buffer[9:]
        elif(force_errors==3):
            end_value = (405).to_bytes(4, byteorder="big")
            buffer = buffer[-4:]+end_value
        elif(force_errors==4):
            wrong_value = (203).to_bytes(1, byteorder="big")
            buffer = buffer[0:10]+buffer[10:-5]+wrong_value+buffer[-4:]
        return buffer    
        
    def handshake_analyzer(self,buffer,numberofpackages,size):
        num_value = int.from_bytes(buffer[:4], byteorder="big")
        size_value = int.from_bytes(buffer[4:10], byteorder="big")
        end_value = int.from_bytes(buffer[-4:], byteorder="big")
        
        if (num_value == numberofpackages)and(size_value==size)and(end_value==404):
            respost = "Recebido do Server a resposta do handshake corretamente."
            return respost
        elif (num_value == 0)and(size_value==0)and(end_value==0):
            respost = "O Server não está pronto para receber um handshake."
            return respost
        else:
            errormsg = "Ocorreu(eram) os seguinte(s) erros: "
            if (num_value != numberofpackages):
                errormsg += "Quantidade total de pacotes incorreta no Head. "
            elif (size_value!=size):
                errormsg += "Tamanho de arquivo incorreto no Head. "
            elif (end_value!=404):
                errormsg += "Valor final incorreto."    
            return errormsg
        
    def package_creator(self,buffer):
        
        buffer_len = len(buffer)
        packages = []
        finalpackage_size = buffer_len%114
        
        if (finalpackage_size != 0):
            numberofpackages = (buffer_len//114)+1
        else:
            numberofpackages = (buffer_len//114)
            
        # Criando os pacotes e organizando
        for i in range(0,numberofpackages+1):
            
            if (i==0):
                total_package_H = (numberofpackages).to_bytes(4, byteorder="big")
                size_package_H = buffer_len.to_bytes(6, byteorder="big")
                eop = (404).to_bytes(4, byteorder="big")
                handshake = total_package_H+size_package_H+eop
                packages.append(handshake)
            else:
                # EOL
                end_package = (404).to_bytes(4, byteorder="big") 
                # Payload
                if (buffer_len>114):
                    if (i < numberofpackages):
                        payload_package = buffer[114*(i-1):i*114]
                        pkg_size = 114
                    else:
                        extra_part = (0).to_bytes(114-finalpackage_size, byteorder="big")
                        payload_package = buffer[114*(i-1):(114*(i-1)+finalpackage_size)]+extra_part
                        pkg_size = finalpackage_size
                else:
                    extra_part = (0).to_bytes(114-finalpackage_size, byteorder="big")
                    payload_package = buffer[0:finalpackage_size]+extra_part
                    pkg_size = finalpackage_size
                    
                # head
                current_package = (i).to_bytes(4, byteorder="big")
                total_package  = (numberofpackages).to_bytes(5, byteorder="big")
                read_package = (pkg_size).to_bytes(1, byteorder="big")
                head = current_package+total_package+read_package    
                    
                # Assemble
                package = head+payload_package+end_package
                packages.append(package)
            
        return packages, numberofpackages, buffer_len    
        
    def init_comm(self):
            try:
                print("-------------------------")
                print("Client Started")
                print("-------------------------")
                
                # Declaramos um objeto do tipo enlace com o nome "com". Essa é a camada inferior à aplicação. Observe que um parametro
                # para declarar esse objeto é o nome da porta.
                self.CTX = enlace(self.comTX, self.Baud_Rate)
                self.CRX = enlace(self.comRX, self.Baud_Rate)
                
                # Ativa comunicacao. Inicia os threads e a comunicação serial 
                self.CTX.enable()
                self.CRX.enable()
                self.count = 1
                
                # Se chegamos até aqui, a comunicação foi aberta com sucesso. Faça um print para informar.
                client_init_msg1 = "Client TX iniciado na porta: {}.".format(self.comTX)
                client_init_msg2 = "Client RX iniciado na porta: {}.".format(self.comRX)
                
                print(client_init_msg1)
                print(client_init_msg2)  
                print("-------------------------")
                
                # Carregando imagem a ser executada
                image_name = self.location_r.split("\\")
                self.txBuffer = open(self.location_r, "rb").read()
                self.txBuffer_len = len(self.txBuffer)
                client_init_msg3 = "Imagem para transmissão: {} ({} bytes).".format(image_name[1], self.txBuffer_len)
                print(client_init_msg3)
                print("-------------------------")
                
                # Criando os pacotes do sistema
                client_init_msg4 = "Criando os pacotes do sistema."
                print(client_init_msg4)
                print("-------------------------")
                self.pacotes, self.numberofpackages, self.size = self.package_creator(self.txBuffer)
                
                return([client_init_msg1,client_init_msg2,client_init_msg3,client_init_msg4, self.numberofpackages])
            
            except Exception as erro:
                print("ops! :-\\")
                print(erro)
                self.CTX.disable()
                self.CRX.disable()   
                
    def handshake_send_response(self):
            try:
                # Enviando para o Server o Header
                client_comm_msg1 = "Enviando o para o Server o Handshake."
                print(client_comm_msg1)
                print("-------------------------")
                self.CTX.sendData(np.asarray(self.pacotes[0])) 
                
                # Recebendo uma resposta do Server sobre o Handshake
                client_comm_msg2 = "Esperando a resposta do Server sobre o Handshake."
                print(client_comm_msg2)
                self.rxBuffer_H, nRx = self.CRX.getData(14)
                client_comm_msg3 = self.handshake_analyzer(self.rxBuffer_H, self.numberofpackages, self.size)
                print(client_comm_msg3)
                print("-------------------------")
                
                return([client_comm_msg1,client_comm_msg2,client_comm_msg3])
            
            except Exception as erro:
                print("ops! :-\\")
                print(erro)
                self.CTX.disable()
                self.CRX.disable()
    
    def execution_start(self):
        try:
            # Começar o cronometro do tempo de execução do envio
            client_time_msg1 = "Iniciando o timer de execução."
            print(client_time_msg1)
            self.start_time = time.time()
            
            client_time_msg2 = "Iniciando envio de pacotes."
            print(client_time_msg2)
            print("-------------------------")
            
            return([client_time_msg1,client_time_msg2])
            
        except Exception as erro:
            print("ops! :-\\")
            print(erro)
            self.CTX.disable()
            self.CRX.disable()           
                
    def data_send_response(self, count):
            try:
                my_errors = [0,1,2,3,4]
                error_value = random.choices(my_errors, weights = [100,10,0,0,0])[0]
                self.txBuffer_S = self.package_errors(self.pacotes[count],error_value)
                self.CTX.sendData(np.asarray(self.txBuffer_S))
                time.sleep(0.1)
                self.rxBuffer_D, nRx = self.CRX.getData(128)
                package_check = self.package_analyzer(self.rxBuffer_D, self.numberofpackages, count-1, self.txBuffer_len)
                if (package_check=="Tudo correto."):
                    client_data_msg1 = "Pacote enviado corretamente."
                    print(client_data_msg1)
                    client_data_msg2 = "Pacote atual: {} de {}.".format(count,self.numberofpackages)
                    print(client_data_msg2)
                    count+=1
                else:
                    client_data_msg1 = package_check
                    print(client_data_msg1)
                    client_data_msg2 = "Pacote atual: {} de {}.".format(count,self.numberofpackages)
                    print(client_data_msg2)
                print("-------------------------")   
                
                return([client_data_msg1,client_data_msg2,count])
            
            except Exception as erro:
                print("ops! :-\\")
                print(erro)
                self.CTX.disable()
                self.CRX.disable()
    
    def execution_end(self):
        try:
            # Acesso aos bytes recebidos
            client_ex_msg1 = "Esperando a resposta de conclusão da conexão."
            print(client_ex_msg1)
            self.rxBuffer_D, nRx = self.CRX.getData(14)
            
            client_ex_msg2 = self.handshake_analyzer(self.rxBuffer_H, self.numberofpackages, self.size)
            print(client_ex_msg2)
            print("-------------------------")
            
            
            return([client_ex_msg1,client_ex_msg2])
            
        except Exception as erro:
            print("ops! :-\\")
            print(erro)
            self.CTX.disable()
            self.CRX.disable()            
                
    def end_connection(self):
            try:
                client_end_msg1 = "Concluindo a conexão com o Server."
                print(client_end_msg1)
                print("-------------------------")
                
                # Encerra tempo de cronometro
                print("Procedimento finalizado")
                self.execution_time = time.time() - self.start_time
                client_end_msg2 = "Tempo de execução: {:.2f} segundos.".format(self.execution_time)
                print(client_end_msg2)
                client_end_msg3 = "Velocidade de transmissão: {:.2f} Bytes/segundos.".format(self.txBuffer_len/self.execution_time)
                print(client_end_msg3)
                
                # Encerra comunicação
                print("-------------------------")
                client_end_msg4 = "Comunicação encerrada com as portas {} e {}.".format(self.comTX,self.comRX)
                print(client_end_msg4)
                print("-------------------------")
                self.CTX.disable()
                self.CRX.disable() 
                
                return([client_end_msg1,client_end_msg2,client_end_msg3,client_end_msg4])
            
            except Exception as erro:
                print("ops! :-\\")
                print(erro)
                self.CTX.disable()
                self.CRX.disable()                          