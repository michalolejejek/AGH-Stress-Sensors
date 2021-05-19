unsigned long t = 0;
unsigned long t_old = -1;
int Fp = 100; //częstotliwość próbkowania
int T = 1000/Fp;
int counter1 = 0;
int counter2 = 0;
int counter3 = 0;
int counter4 = 0;

void setup()
{
  Serial.begin(57600);
  pinMode(10, INPUT);
  pinMode(11, INPUT);
  pinMode(A0, INPUT);
}

void loop()
{
  t = millis();
  if (t%T == 0 && t != t_old)
  {
    if((digitalRead(10) == 1)||(digitalRead(11) == 1))
    {
      Serial.print(t);
      Serial.print('x');
      Serial.println(0);
    }
    else
    {
      Serial.print(t);
      Serial.print('x');
      Serial.println(analogRead(A0));
    }   
  }
  t_old = t;
}