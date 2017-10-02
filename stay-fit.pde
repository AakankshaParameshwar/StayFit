
import netP5.*;
import oscP5.*;

int linecount =1000;
int loading;
OscP5 test;
NetAddress myRemoteLocation;
PImage[] images = new PImage [7];
 PImage p, maskImg, maskImg1, maskImg2, img;
 //var x;
void setup() {
  size(1000, 800);
  frameRate(25);
  frame.setResizable(true);
  background(0);
  colorMode(HSB);
  int count=0;
  //bird_createimg = createImg("assets/bird_2.gif");
// p=loadImage("images/minions_"+1+".png");
img = loadImage("images/giphy_4.jpg");
maskImg = loadImage("images/mask.jpg");
maskImg1 = loadImage("images/mask_1.jpg");
maskImg2 = loadImage("images/mask_2.jpg");
  for(int i =1; i<=7;i++){
    p = loadImage("images/minions_"+i+".png");
     images[count++] = p;
     System.out.println("image_"+i+" loaded");
   }
  // img.mask(maskImg);
  print("--> "+p);
  test = new OscP5(this, 12000);
  myRemoteLocation = new NetAddress("127.0.0.1",12000);
  //test.plug(this, "joggingVisualization", "/jog");
}


void draw() {
 if(loading == 0){
   background(0);
   fill(255);
   textSize(32);
   textAlign(CENTER, CENTER);
   text("Unveil magic by jogging", width/2, height/2); 

 }
 
else if( loading >0 && loading <=400){
   /*for(int i=0;i<=loading; i++){
     image(images[int(random(images.length-1))],random(width), random(height));
   }*/
   if(loading % 5 == 0 && loading != 400){
     image(images[int(random(images.length-1))],random(width),random(height));
   }
  // image(maskImg, width/6 + loading*2,height/4);
   image(img, width/6,width/6);
   fill(0);
   rect(width/6, width/6,800-(loading*2), 506);
   if(800-(loading*2)<=0){
     image(maskImg2, width/6,width/6);
   }
   
 }
 

}

/*void mousePressed() {
  image(images[int(random(images.length-1))],random(width),random(height));
}*/


/*incoming osc message are forwarded to the oscEvent method.*/
void oscEvent(OscMessage theOscMessage) {
  /* print the address pattern and the typetag of the received OscMessage */
  print("### received an osc message.");
  print(" addrpattern: "+theOscMessage.addrPattern());
  println(" typetag: "+theOscMessage.typetag());
  loading = theOscMessage.get(0).intValue();
  println(" value: "+loading);
  //image(images[int(random(images.length-1))],random(width),random(height));

}