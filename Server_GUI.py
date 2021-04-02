import PySimpleGUI as sg
import os.path
import Server

sg.theme('Dark')

# First the window layout in 2 columns

file_list_column = [
    [
        sg.Text("Selecionar Pasta"),
        sg.In(size=(25, 1), enable_events=True, key="-FOLDER-"),
        sg.FolderBrowse(),
    ],
    [
        sg.Text("Modo"),
        sg.Combo(['ARDUINO', 'INTERNO'], enable_events=True,size=(10, 4), key='combo1'),
    ],
    [
        sg.Text("Baud Rate"),
        sg.Combo([9600,115200,230400], enable_events=True,size=(10, 4), key='combo2'),
    ],
    [
        sg.Text("Porta Server TX"),
        sg.Combo(['COM1', 'COM2', 'COM3','COM4'], enable_events=True,size=(10, 4), key='combo3'),
    ],
    [
        sg.Text("Porta Server RX"),
        sg.Combo(['COM1', 'COM2', 'COM3','COM4'], enable_events=True,size=(10, 4), key='combo4'),
    ],
    [sg.Button('Atribuir Portas',size=(15, 2),enable_events=True, key="-BEGIN-")],
    [sg.Button('Esperar Handshake',size=(15, 2),visible=False,enable_events=True, key="-HAND-")],
    [sg.Text(size=(40, 1), key="-BEGINTXT-")],
]

# For now will only show the name of the file that was chosen
image_viewer_column = [
    [sg.Text("Imagem recebida do Cliente:")],
    [sg.Text(size=(40, 1), key="-TOUT-")],
    [sg.Image(key="-IMAGE-")],
]

Server_column = [
    [sg.Text("Comunicação Servidor:")],
    [sg.Text(size=(50, 1), key="-ROUT1-")],
    [sg.Text(size=(50, 1), key="-ROUT2-")],
    [sg.Text(size=(50, 1), key="-ROUT3-")],
    [sg.Text(size=(50, 1), key="-ROUT4-")],
    [sg.Text(size=(50, 1), key="-ROUT5-")],
    [sg.Text(size=(50, 1), key="-ROUT6-")],
    [sg.Text(size=(50, 1), key="-ROUT7-")],
    [sg.Text(size=(50, 1), key="-ROUT8-")],
    [sg.Text(size=(50, 1), key="-ROUT9-")],
    [sg.Text(size=(50, 1), key="-ROUT10-")],
    [sg.Text(size=(50, 1), key="-ROUT11-")],
    [sg.Text(size=(50, 1), key="-ROUT12-")],
]

# ----- Full layout -----
layout = [
    [
        sg.Column(file_list_column),
        sg.VSeperator(),
        sg.Column(Server_column),
        sg.VSeperator(),
        sg.Column(image_viewer_column),
    ]
]

window = sg.Window("Projeto 2 - Servidor", layout)

count = 1
state_machine = 0
temp = 0

# Run the Event Loop
while True:
    if (temp == 1)and(state_machine!=1)and(state_machine!=3):
        state_machine += 1
    if (temp == 2):
        state_machine += 1
        temp=1 
    if (state_machine == 6):
        count = 1
        state_machine=0
        temp=0 
    event, values = window.read(timeout = 200)
    if event == "Exit" or event == sg.WIN_CLOSED:
        break
    # Folder name was filled in, make a list of files in the folder
    if event == "-FOLDER-":
        folder = values["-FOLDER-"]
        try:
            filename = os.path.join(values["-FOLDER-"],"Copia_recebida.png")
        except:
            file_list = []
        
    elif event == "-BEGIN-":  
        try:
            modo = values['combo1']
            STX = values['combo3']
            SRX = values['combo4']
            if (((STX==SRX)and(filename!=None)and(modo=="ARDUINO"))or((STX!=SRX)and(filename!=None)and(modo=="INTERNO"))):
                
                baudrate = values['combo2']
                
                # Aviso para de início da GUI
                begintxt = "O protocolo foi inicializado."
                window["-BEGINTXT-"].update(begintxt)   
                
                # Iniciando a comunicação com Servidor
                server_info = Server.Server(filename,STX,SRX,baudrate)
                server_init_resp = server_info.init_comm()
                window["-ROUT1-"].update(server_init_resp[0])
                window["-ROUT2-"].update(server_init_resp[1])
                window["-ROUT3-"].update(server_init_resp[2])
                window["-ROUT4-"].update(server_init_resp[3])
                state_machine = 0
                temp = 1
            else:
                begintxt = "O arranjo escolhido não pode ser inicializado."
                window["-BEGINTXT-"].update(begintxt)
        except:
            pass
        
    elif (state_machine == 1) or (event == "-HAND-"):     
        try:
            # Enviando e recebendo o Handshake
            server_handshake_resp = server_info.handshake_receive_response()
            window["-ROUT5-"].update(server_handshake_resp[0])
            numberofpackages = server_handshake_resp[1]           
            window.Refresh()
            if (server_handshake_resp[1]!="O Handshake do Client não foi recebido corretamente."):
                state_machine=1
                temp=2
                window["-HAND-"].update(visible=False)
            else:
                window["-HAND-"].update(visible=True)
                state_machine=0
                temp=0
        except:
            pass
    elif state_machine == 2:  
        try:        
            # Iniciando o cronômetro
            server_time_resp = server_info.execution_start()
            window["-ROUT6-"].update(server_time_resp[0])
            window["-ROUT7-"].update(server_time_resp[1])
            window.Refresh()
        except:
            pass    
    elif state_machine == 3:  
        try:
            # Enviando os pacotes
            if(count<=numberofpackages):
                server_org_resp = server_info.data_receive_response(count)
                count = server_org_resp[2]
                window["-ROUT8-"].update(server_org_resp[0])
                window["-ROUT9-"].update(server_org_resp[1])   
            if (count>numberofpackages):
                temp=2
            window.Refresh()    
        except:
            pass
    elif state_machine == 4:  
        try:        
            # Finalizando a conexão
            server_ex_resp = server_info.execution_end()
            window["-ROUT10-"].update(server_ex_resp[0])
            window.Refresh()
        except:
            pass          
    elif state_machine == 5: 
        try:
            # Escrevendo dados na imagem e concluindo a conexão
            server_end_resp = server_info.end_connection()
            window["-ROUT11-"].update(server_end_resp[0])
            window["-ROUT12-"].update(server_end_resp[1])
            window["-TOUT-"].update("Copia_recebida.png")
            window["-IMAGE-"].update(filename=filename)
            window.Refresh()
        except:
            pass 

window.close()