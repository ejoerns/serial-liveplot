#include "asdl.h"
#include "contiki.h"
#include <stdio.h> /* For printf() */
#include "rs232.h"
#include "acc-sensor.h"
#include "gyro-sensor.h"

// allows to send data via rs232
void my_send(char dat) {
  rs232_send(RS232_PORT_0, (unsigned char) dat);
}

/*---------------------------------------------------------------------------*/
PROCESS(hello_world_process, "Hello world process");
AUTOSTART_PROCESSES(&hello_world_process);
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(hello_world_process, ev, data)
{
  PROCESS_BEGIN();

  static struct etimer et;


  // get pointer to sensor
  static const struct sensors_sensor *acc_sensor;
  acc_sensor = sensors_find("Acc");
  static const struct sensors_sensor *gyro_sensor;
  gyro_sensor = sensors_find("Gyro");

  uint8_t status;
  // activate and check status
  status = SENSORS_ACTIVATE(*acc_sensor);
  if (status == 0) {
    printf("Error: Failed to init accelerometer, aborting...\n");
    PROCESS_EXIT();
  }
  // activate and check status
  status = SENSORS_ACTIVATE(*gyro_sensor);
  if (status == 0) {
    printf("Error: Failed to init gyroscope, aborting...\n");
    PROCESS_EXIT();
  }

  // Example:
  CREATE_LOGGER(my_logger, "My Logger", 4, &my_send);
  //struct asdl_channel my_logger_channels[4];
  //struct asdl_logger my_logger = { 4, "My Logger", &my_logger_channels};
  asdl_add_ch(&my_logger, 0, ASDL_VEC3 | ASDL_SIGNED | ASDL_INT32, 1, -2000, 2000, "Acc  [x:y:z]", "mg");
  asdl_add_ch(&my_logger, 1, ASDL_VEC2 | ASDL_SIGNED | ASDL_INT32, 1, -500, 500, "Gyro [x:y]", "mdps");
  asdl_add_ch(&my_logger, 2, ASDL_VEC1 | ASDL_SIGNED | ASDL_INT16, 1, -55, 185, "Temp",  "C");

  asdl_start_logger(&my_logger);

  int32_t val0[3] = {123, 234, 222};
  int32_t val1[2] = {500, 500};

  while(1)
  {
    val0[0] = acc_sensor->value(ACC_X);
    val0[1] = acc_sensor->value(ACC_Y);
    val0[2] = acc_sensor->value(ACC_Z);
    //printf("x: %ld, y: %ld, z: %ld\n", val0[0], val0[1], val0[2]);
    asdl_log(&my_logger, 0, val0);

    val1[0] = gyro_sensor->value(GYRO_X);
    val1[1] = gyro_sensor->value(GYRO_Y);
    asdl_log(&my_logger, 1, &val1);

    int16_t val2 = 42;
    asdl_log(&my_logger, 2, &val2);

    etimer_set(&et, CLOCK_SECOND / 64);

    PROCESS_YIELD();
  }


  PROCESS_END();
}
/*---------------------------------------------------------------------------*/

