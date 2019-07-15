import sqlite3
from datetime import datetime, timedelta
from digi.xbee.devices import XBeeDevice, XBee64BitAddress, RemoteXBeeDevice
from digi.xbee.io import IOLine, IOMode, IOValue, IOSample
from digi.xbee.exception import TimeoutException
from digi.xbee.models.status import ModemStatus
import time
#----------------------------------------------------------------------------------------
MAX_RETRIES = 3

def main():

	PORT = "/dev/ttyUSB0"
	# TODO: Replace with the baud rate of your local module.
	BAUD_RATE = 9600

	IOLINE_OUT1 = IOLine.DIO4_AD4
	IOLINE_OUT2 = IOLine.DIO1_AD1

	date_jour = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
	duration = 40
	conn = sqlite3.connect('/home/ProjetArrosage.db')
	c = conn.cursor()
	db = conn.cursor()
	a = list()
	b = list()
	d = list()
	f = list()
	e = list()
	g = list()
	# creation de la table arrosage

	c.execute('''CREATE TABLE IF NOT EXISTS ARROSAGE
	             ([id] INTEGER PRIMARY KEY,[id_routeur] integer,[id_parc] integer,[id_zone] integer,[id_cluster] integer,[id_vanne] integer,
	             [IO] integer,[is_forced] boolean,[trigged] boolean,[Date] date,[duree] text )''')

	c.execute('''CREATE TABLE IF NOT EXISTS MACID
	             ([id] INTEGER PRIMARY KEY,[id_vanne] integer,[mac_addr] text)''')

	conn.commit()

	c.execute("""SELECT id_vanne,Date FROM ARROSAGE""")
	donnee_arr = c.fetchall()
	for date in donnee_arr:
		d.append(date[1])



	def HighLow():
		remote_device.set_dio_value(IOLINE_OUT1,IOValue.HIGH)
		remote_device.set_dio_value(IOLINE_OUT2,IOValue.LOW)

		value_OUT2 = remote_device.get_dio_value(IOLINE_OUT2)
		value_OUT1 = remote_device.get_dio_value(IOLINE_OUT1)
		print(value_OUT2)
		print(value_OUT1)
		time.sleep(0.4)

	def LowHigh():
		remote_device.set_dio_value(IOLINE_OUT1,IOValue.LOW)
		remote_device.set_dio_value(IOLINE_OUT2,IOValue.HIGH)

		value_OUT2 = remote_device.get_dio_value(IOLINE_OUT2)
		value_OUT1 = remote_device.get_dio_value(IOLINE_OUT1)
		print(value_OUT2)
		print(value_OUT1)
		time.sleep(0.4)

	def off():
		remote_device.set_dio_value(IOLINE_OUT1,IOValue.LOW)
		remote_device.set_dio_value(IOLINE_OUT2,IOValue.LOW)


	while 1:
		flag = 0
		date_jour = datetime.now().strftime('%d/%m/%Y %H:%M:%S') # cast date actuel en str
		for date in d:							# ensemble des dates presentes dans la base de données
			if date_jour == date:			# egalité entres les dates d'arrosage et l'heure actuel
				c.execute("SELECT id_vanne FROM ARROSAGE where date like ?", ('%' + date + '%', )) # recuperation de l'id vanne et de la durée pour la date effective
				db.execute("SELECT duree FROM ARROSAGE where date like ?", ('%' + date + '%', ))
				date_obj = datetime.strptime(date,"%d/%m/%Y %H:%M:%S")
				dataVanne = c.fetchall()
				dataDuree = db.fetchall()
				print(dataVanne)
				print(dataDuree)
				for id_vanne in dataVanne:
					f.append(id_vanne[0])
					vanne_id = f[0]
				for duree in dataDuree:
					g.append(duree[0])
					duree = g[0]
					duree = datetime.strptime(duree,'%M')
					dureeMin = timedelta(minutes=duree.minute)
					print(vanne_id)
					print(duree)
				# comparaison id_vanne de la table ARROSAGE et id_vanne MACID recuperation de l'adresse mac
				c.execute("SELECT mac_addr FROM MACID where id_vanne like ?", ('%' + str(vanne_id) + '%', )) 
				m = c.fetchall()
				for mm in m:
					e.append(mm[0])
				xbee_adr = e[0] # récuperation de l'adresse mac dans une variable
				print(xbee_adr)
				time.sleep(1)

				stop = False
				th = None
				local_device = XBeeDevice(PORT, BAUD_RATE)

				try:
					local_device.open()
					dead_line = time.time() + duration
					while dead_line > time.time():
						retries = MAX_RETRIES
						data_received = False
						while not data_received:

							try:
								xbee_network = local_device.get_network()
								remote_device = RemoteXBeeDevice(local_device, XBee64BitAddress.from_hex_string(xbee_adr))
								print(remote_device)

								HighLow()
								off()
								# tempsArrosage = int(datetime.now()-date_obj)
								# print(tempsArrosage)
								while flag != 1:
									tempsArrosage =datetime.now()-date_obj
									if tempsArrosage >= dureeMin:
										LowHigh()
										off()
										flag = 1
										data_received = True
									else:
										time.sleep(2)
										print(duree)

							except TimeoutException as ex:
								 retries -= 1
								 if retries == 0:
								 	raise ex
					time.sleep(3)

				finally:
					stop = True
					if th is not None and th.is_alive():
						th.join()
					if local_device is not None and local_device.is_open():
						local_device.close()


if __name__ == '__main__':
    main()
