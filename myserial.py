import serial, time, struct

sbfout_command = b'$R: sso, Stream1, COM1, xPPSOffset, sec1\r\n'
# 定义sbf流输出及终止指令
sbfend_command = b'$R: sso, Stream1, COM1, xPPSOffset, off\r\n'
# '$R: sso, Stream1, COM3, xPPSOffset, off'

def openser(port, baudrate): # 打开串口函数
    ser = serial.Serial(port, baudrate)
    if ser.isOpen():
        print("Connecting to serial:", ser.name)
    else:
        print("Serial Connecting ERROR !!!")
    return ser

def serclose(ser): # 关闭串口函数
    ser.close()
    if ser.isOpen():
        print("Serial Disconnecting ERROR !!!")
    else:
        print("Serial disconnected.")
        print()
        
def streamclose(ser):
    ser.write(sbfend_command) # 停止数据流            
    count = ser.inWaiting() # 判断是否关闭数据流
    while count > 0:
        ser.write(sbfend_command) # 停止数据流
    print('Data stream off.')
    serclose(ser) # 关闭串口
    print('-' * 15 + 'terminated.' + '-' * 15)
        
def hex_to_float(h): # IEEE754 hex2float
    i = int(h, 16)
    return struct.unpack('<f',struct.pack('<I', i))[0]
  
def main():
    ser = openser("COM3", 115200) # 打开串口   
    
    while True:
        try:
            ser.write(sbfout_command) # 建立sbf流
            time.sleep(1) # 等待1s
            count = ser.inWaiting()
            # print(count) # 读取长度

            # 数据的接收
            if count > 0:
                buffer = ser.read(count)
                # print(buffer)
                if buffer != b'':       
                    header_pos = buffer.find(b'$@') # 找帧头\x24\x40
                    if header_pos == -1:
                        print('Packet Not Found !!!')
                        continue
                    
                    try:
                        data = buffer[header_pos : header_pos + 20] # 读主块，取包括起点在内的20个字节，[0][1]为帧头
                        # print('header_pos', header_pos)
                        # crc = data[2:4]
                        
                        id = ((data[5] << 8) + data[4]) # 取数据信息
                        print(id)                        
                        if id == 5911:
                            blockname = 'xPPSOffset'
                        print('Block name: ', blockname)
                        
                        # leng = data[6:8]
                        tow = ((data[11] << 24) + (data[10] << 16) + (data[9] << 8) + data[8])
                        towvalue = tow * 0.001
                        print('TOW: ', towvalue)
                        
                        wnc = (data[13] << 8) + data[12]
                        print('WNc: ', wnc)
                        # syncage = data[14]
                        
                        timescale = data[15]
                        if timescale == 1: ts = 'GPS Time'
                        elif timescale == 2: ts = 'UTC'
                        elif timescale == 3: ts = 'RxClock'
                        elif timescale == 4: ts = 'GLONASS Time'
                        elif timescale == 5: ts = 'Galileo Time'
                        elif timescale == 6: ts = 'BeiDou Time'
                        print('Time Scale: ', ts)
                        
                        # 最后四位转为16进制字符串
                        i = 19
                        offset = ''
                        while i > 15:
                            offset += '{:02X}'.format(data[i])
                            i -= 1
                            
                        offsetvalue = hex_to_float(offset) # IEEE754 float32
                        print('offsetstr =', offset)
                        print('offsethex =', hex(data[16]), hex(data[17]), hex(data[18]), hex(data[19]))
                        print('xPPSOffset Value:', offsetvalue, 'ns')
                        print()
                        # output = ('{}\t{}\t{}\t{}\t\n').format(wnc, towvalue, ts, offsetvalue)
                        # with open ('./log.txt', 'a+') as f: # 输出存到log.txt
                        #     f.write(output)
                        #     f.close()
                        
                    except Exception as err:    
                        streamclose(ser) # 结束函数
                        print("ERROR: %s" % err)
                        break
                    
        except KeyboardInterrupt: # KI打断程序
            streamclose(ser) # 结束函数
            raise                
    
if __name__ == '__main__':
    main()