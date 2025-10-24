#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// defining bools
bool sb = true;
bool idb = true;
bool paused = false;

bool rs = false;
bool rid = false;

bool sonicating = false;
bool iding = false;
bool fronting = false;

int blink = 0;

// State change detection
int lastPausedVal = 0;

// OLED
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Inital Strings to display on OLED
String sDefault = "Waiting...";
String idDefault = "Waiting...";

// Variables to track progress through sample prep
int sFinished = 0;
int idFinished = 0;
int fFinished = 0;
int filled = 0;

// The number of channels we are 
const int N_CHANNELS = 4;

void setup() {
  // setting up the oled
  setUpScreen();

  Serial.begin(9600);
  pinMode(2, INPUT_PULLUP);
  pinMode(7, INPUT_PULLUP);
  pinMode(8, INPUT_PULLUP);
  pinMode(LED_BUILTIN, OUTPUT);

  // Sonication pin setup
  pinMode(3, OUTPUT);
  pinMode(4, OUTPUT);

  // Intake and dispense pin setup
  pinMode(9, OUTPUT);
  pinMode(10, OUTPUT);

  // Finished molds pin setup
  pinMode(11, OUTPUT);
  pinMode(12, OUTPUT);

  // Resetting LED pins to be off
  digitalWrite(3, LOW);
  digitalWrite(4, LOW);
  digitalWrite(9, LOW);
  digitalWrite(10, LOW);
}

void loop() {
  // put your main code here, to run repeatedly:
  int sbVal = digitalRead(2);
  int idbVal = digitalRead(7);
  int pausedVal = digitalRead(8);


  if (rs && (sbVal == HIGH)) {
    sb = true;
    Serial.write("SONICATIONBEGUN");
  } else {
    sb = false;
  }
  if (rid && (idbVal == HIGH)) {
    idb = true;
    Serial.write("IDBEGUN");
  } else {
    idb = false;
  }
  if (pausedVal == HIGH) {
    Serial.write("PAUSED");
    paused = true;
  }
  else if ((pausedVal == LOW) && (lastPausedVal == HIGH)) {
    Serial.write("UNPAUSED");
    paused = false;
  }

  if (Serial.available() > 0){
    String msg = Serial.readString();

    if (msg == "FILLED") {
      filled += 1;
      if (filled % N_CHANNELS == 0) {
        iding = false;
        idFinished += 1;
        filled = 0;
        if (idFinished == 2) {
          idDefault = "Done";
        }
      }
    }
    
    else if (msg == "READYFORS") {
      rs = true;
    }
    else if (msg == "READYFORID") {
      rid = true;
    }

    else if (msg == "NOTFILLING") {
      iding = false;
      if (idFinished == 2) {
          idDefault = "Done";
        } else {
          idDefault = "Waiting...";
        }
    }
    else if (msg == "NOTDRYING") {
      sDefault = "Sonicating...";
    }

    else if (msg == "DONESON") {
      sonicating = false;
      sDefault = "Waiting...";
      sFinished += 1;

      if (sFinished == 2) {
        sDefault = "Done";
      }
    }
    else if (msg == "FILLING") {
      iding = true;
    }
    else if (msg == "SONICATING") {
      sonicating = true;
      sDefault = "Sonicating...";
    }
    else if (msg == "DRYING") {
      sDefault = "Drying...";
    }

    else if (msg == "PROMPTING") {
      fronting = true;
    }
    else if (msg == "MOLDDONE") {
      fronting = false;
      fFinished += 1;
    }
  }

  if (paused) {
    display.clearDisplay();
    display.setCursor(5,10);
    display.setTextSize(2);
    display.print("PAUSED");
    display.display();
    blink = 3;
  } else {
    display.clearDisplay();
    sbDisplay();
    idDisplay();
    display.display();

    updateSLights();
    updateIDLights();
    updateFLights();

    blink += 1;
    delay(200);
  }

  lastPausedVal = pausedVal;
}

void sbDisplay() {
  if (sb) {
    rs = false;
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.print("Beginning Sonication");
  } else if (rs) {
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.print("Ready for Sonication");
  } else {
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.print(sDefault);
  }
}

void idDisplay() {
  if (idb && rid) {
    rid = false;
    display.setTextSize(1);
    display.setCursor(0, 10);
    display.print("Beginning I&D");
    Serial.println("Beginning ID");
  } else if (rid) {
    display.setTextSize(1);
    display.setCursor(0, 10);
    display.print("Ready for I&D");
  } else if (filled != 0) {
    display.setTextSize(1);
    display.setCursor(1, 10);
    display.print("Have filled " + String(filled));
  } else {
    display.setTextSize(1);
    display.setCursor(0, 10);
    display.print(idDefault);
  }
}

void updateSLights() {
  // Keep first sonicating light solid
  if (sFinished == 1) {
    digitalWrite(3, HIGH);
    // Blink the second sonicating light
    if (sonicating) {
      if ((blink % 4 == 0) || (blink % 4 == 1)) {
        digitalWrite(4, HIGH);
      } else {
        digitalWrite(4, LOW);
      }
    }
    else {
      digitalWrite(4, LOW);
    }
  } 
  // Keep both sonicating lights solid
  else if (sFinished == 2) {
    digitalWrite(3, HIGH);
    digitalWrite(4, HIGH);
  } 
  // Neither sonicating light solid
  else {
    // Blink the first sonicating light
    if (sonicating) {
      if ((blink % 4 == 0) || (blink % 4 == 1)) {
        digitalWrite(3, HIGH);
      } else {
        digitalWrite(3, LOW);
      }
    }
    else {
      digitalWrite(3, LOW);
    }
  }
}

void updateIDLights() {
  // Keep first id light solid
  if (idFinished == 1) {
    digitalWrite(9, HIGH);
    // Blink the second id light
    if (iding) {
      if ((blink % 4 == 0) || (blink % 4 == 1)) {
        digitalWrite(10, HIGH);
      } else {
        digitalWrite(10, LOW);
      }
    }
    else {
      digitalWrite(10, LOW);
    }
  } 
  // Keep both id lights solid
  else if (idFinished == 2) {
    digitalWrite(9, HIGH);
    digitalWrite(10, HIGH);
  } 
  // Neither id light solid
  else {
    // Blink the first id light
    if (iding) {
      if ((blink % 4 == 0) || (blink % 4 == 1)) {
        digitalWrite(9, HIGH);
      } else {
        digitalWrite(9, LOW);
      }
    }
    else {
      digitalWrite(9, LOW);
    }
  }
}

void updateFLights() {
  // Keep first front light solid
  if (fFinished == 1) {
    digitalWrite(11, HIGH);
    // Blink the second front light
    if (fronting) {
      if ((blink % 4 == 0) || (blink % 4 == 1)) {
        digitalWrite(12, HIGH);
      } else {
        digitalWrite(12, LOW);
      }
    }
    else {
      digitalWrite(12, LOW);
    }
  } 
  // Keep both front lights solid
  else if (idFinished == 2) {
    digitalWrite(11, HIGH);
    digitalWrite(12, HIGH);
  } 
  // Neither front light solid
  else {
    // Blink the first front light
    if (fronting) {
      digitalWrite(LED_BUILTIN, HIGH);

      if ((blink % 4 == 0) || (blink % 4 == 1)) {
        digitalWrite(11, HIGH);
      } else {
        digitalWrite(11, LOW);
      }
    }
    else {
      digitalWrite(11, LOW);
      digitalWrite(12, LOW);
    }
  }
}

void setUpScreen() {
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display.clearDisplay();
  display.setTextColor(WHITE);
  display.setCursor(0,0);
  display.setTextSize(2);
  display.print("SETTING UP");
  display.display();
}
