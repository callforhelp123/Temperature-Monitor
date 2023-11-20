import board
import digitalio
import adafruit_max31856

def get_temp():
	spi = board.SPI()
	cs = digitalio.DigitalInOut(board.D5)
	cs.direction = digitalio.Direction.OUTPUT
	thermocouple = adafruit_max31856.MAX31856(spi,cs)
	return(thermocouple.temperature)
