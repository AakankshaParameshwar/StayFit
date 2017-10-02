import itertools
import pygame
import pygame.color

from pygame.color import THECOLORS
from pykinect import nui
from pykinect.nui import JointId
from pykinect.nui import SkeletonTrackingState
from pykinect.nui.structs import (TransformSmoothParameters, Vector)
from time import sleep

import OSC

SKELETON_COLORS = [THECOLORS["red"], 
                   THECOLORS["blue"], 
                   THECOLORS["green"], 
                   THECOLORS["orange"], 
                   THECOLORS["purple"], 
                   THECOLORS["yellow"], 
                   THECOLORS["violet"]]

LEFT_ARM = (JointId.ShoulderCenter, 
            JointId.ShoulderLeft, 
            JointId.ElbowLeft, 
            JointId.WristLeft, 
            JointId.HandLeft)
RIGHT_ARM = (JointId.ShoulderCenter, 
             JointId.ShoulderRight, 
             JointId.ElbowRight, 
             JointId.WristRight, 
             JointId.HandRight)
LEFT_LEG = (JointId.HipCenter, 
            JointId.HipLeft, 
            JointId.KneeLeft, 
            JointId.AnkleLeft, 
            JointId.FootLeft)
RIGHT_LEG = (JointId.HipCenter, 
             JointId.HipRight, 
             JointId.KneeRight, 
             JointId.AnkleRight, 
             JointId.FootRight)
SPINE = (JointId.HipCenter, 
         JointId.Spine, 
         JointId.ShoulderCenter, 
         JointId.Head)

SMOOTH_PARAMS_SMOOTHING = 0.7
SMOOTH_PARAMS_CORRECTION = 0.4
SMOOTH_PARAMS_PREDICTION = 0.7
SMOOTH_PARAMS_JITTER_RADIUS = 0.1
SMOOTH_PARAMS_MAX_DEVIATION_RADIUS = 0.1
SMOOTH_PARAMS = TransformSmoothParameters(SMOOTH_PARAMS_SMOOTHING,
                                          SMOOTH_PARAMS_CORRECTION,
                                          SMOOTH_PARAMS_PREDICTION,
                                          SMOOTH_PARAMS_JITTER_RADIUS,
                                          SMOOTH_PARAMS_MAX_DEVIATION_RADIUS)

skeleton_to_depth_image = nui.SkeletonEngine.skeleton_to_depth_image


class SkeletonManager:

    # Constructor
    def __init__(self):
        self.max_skeletons = 2
        self.active_skeletons = {}
        self.old_skeletons = {}

    def create_skeleton(self, skeleton, index):
        self.active_skeletons[index] = Skeleton(skeleton)

    def num_skeletons(self):
        return len(self.active_skeletons)

    def update_skeletons(self, new_skeleton, index):
        for i in self.active_skeletons.keys():
            if( i == index):
                self.old_skeletons[i] = self.active_skeletons[i]
                self.active_skeletons[i] = Skeleton(new_skeleton)

    def find_gestures(self):
        gestures = {}
        for i in self.active_skeletons.keys():
            gesture = []
            index = i
            '''if(self.active_skeletons[i].detect_right_hand_swipe(self.old_skeletons[i])):
                gesture.append('swipe')
            if(self.active_skeletons[i].detect_leg_jogging(self.old_skeletons[i])):
                gesture.append('jog')'''
            if(self.active_skeletons[i].detect_start_jogging(self.old_skeletons[i])):
                gesture.append('start')
            if(self.active_skeletons[i].detect_stop()):
                gesture.append('stop')
            if(self.active_skeletons[i].move_left(self.old_skeletons[i])):
                gesture.append('left')
            if(self.active_skeletons[i].move_right(self.old_skeletons[i])):
                gesture.append('right')
            gestures[index] = gesture
        return gestures
    

    def __str__(self):
        s = ''
        for b in self.active_skeletons:
            for c in self.old_skeletons:
                s += b.index + " --> \nold: " + c + "\nNew: "+b 
        return s


def create_vector_midpoint(one, two):
    mid = Vector()
    mid.x = (one.x + two.x)/2
    mid.y = (one.y + two.y)/2
    mid.z = one.z
    mid.w = one.w
    return mid
    
############## Class for each ball showing on the screen 
class Skeleton:

    def __init__(self, skeleton):
        self.Head = skeleton.SkeletonPositions[JointId.Head]
        self.Spine = skeleton.SkeletonPositions[JointId.Spine]

        self.ShoulderCenter = skeleton.SkeletonPositions[JointId.ShoulderCenter]
        self.ShoulderLeft = skeleton.SkeletonPositions[JointId.ShoulderLeft]
        self.ShoulderRight = skeleton.SkeletonPositions[JointId.ShoulderRight]
        self.ElbowLeft = skeleton.SkeletonPositions[JointId.ElbowLeft]
        self.ElbowRight = skeleton.SkeletonPositions[JointId.ElbowRight]
        self.WristLeft = skeleton.SkeletonPositions[JointId.WristLeft]
        self.WristRight = skeleton.SkeletonPositions[JointId.WristRight]
        self.HandLeft = skeleton.SkeletonPositions[JointId.HandLeft]
        self.HandRight = skeleton.SkeletonPositions[JointId.HandRight]

        self.HipCenter = skeleton.SkeletonPositions[JointId.HipCenter]
        self.HipLeft = skeleton.SkeletonPositions[JointId.HipLeft]
        self.HipRight = skeleton.SkeletonPositions[JointId.HipRight]
        self.KneeLeft = skeleton.SkeletonPositions[JointId.KneeLeft]
        self.KneeRight = skeleton.SkeletonPositions[JointId.KneeRight]
        self.AnkleLeft = skeleton.SkeletonPositions[JointId.AnkleLeft]
        self.AnkleRight = skeleton.SkeletonPositions[JointId.AnkleRight]
        self.FootLeft = skeleton.SkeletonPositions[JointId.FootLeft]
        self.FootRight = skeleton.SkeletonPositions[JointId.FootRight]

        self.MidKneeRight = create_vector_midpoint(self.KneeRight, self.FootRight)
        self.MidKneeLeft = create_vector_midpoint(self.KneeLeft, self.FootLeft)
        self.SwipeAction = 0
        
    def detect_right_hand_swipe_1(self):
        if self.HandLeft.y > self.ElbowLeft.y and self.HandRight.y > self.ElbowRight.y and self.HandRight.x > self.ElbowRight.x:
            return True
        return False

    def detect_right_hand_swipe_2(self):
        if self.HandLeft.y > self.ElbowLeft.y and self.HandRight.y > self.ElbowRight.y  and self.HandRight.x < self.ElbowRight.x:
            return True
        return False

    '''def detect_leg_jogging(self, old_skeleton):
        if self.KneeRight.y > self.MidKneeRight and self.KneeLeft.y < self.MidKneeLeft.y:
            #if old_skeleton.KneeRight.y < old_Skeleton.MidKneeRight.y:
            
            return "Right Left up"
        elif self.KneeLeft.y > self.MidKneeLeft and self.KneeRight.y < self.MidKneeRight.y:
            #if old_skeleton.KneeLeft.y < old_Skeleton.MidKneeLeft.y:
            return "Left Left up"
        return ""'''

    def detect_stop(self):
        if self.HandRight.y > self.Head.y and self.HandLeft.y > self.Head.y:
            return True
        return False

    def detect_start_jogging(self, old_skeleton):
        if self.HandLeft.y > self.ElbowLeft.y and self.HandRight.y > self.ElbowRight.y and self.HandLeft.x < self.HandRight.x:
            #if self.detect_leg_jogging(old_skeleton):
            return True
        return False

    def move_left(self, old_skeleton):
        if self.HandLeft.y > self.ElbowLeft.y and self.HandRight.y > self.HandLeft.y:
            if self.ElbowRight.y > self.ElbowLeft.y:
            #if self.detect_leg_jogging(old_skeleton):
                return True
        return False

    def move_right(self, old_skeleton):
        if self.HandRight.y > self.ElbowRight.y and self.HandLeft.y > self.HandRight.y:
            if self.ElbowLeft.y > self.ElbowRight.y:
            #if self.detect_leg_jogging(old_skeleton):
                return True
        return False

    def detect_jogging(self):
        if(self.KneeLeft.y >= (self.KneeRight.y+0.10)):
           return True
        elif(self.KneeRight.y >= (self.KneeLeft.y+0.10)):
            return True
        return False

    '''def detect_t_pose(self, old_skeleton):
        if self.HandRight.x < 0 and self.HandLeft.y > self.HandRight.y:
            if self.ElbowLeft.y > self.ElbowRight.y:
            #if self.detect_leg_jogging(old_skeleton):
                return True
        return False'''

    

    def __str__(self):
        s = "-----------------\n"
        s += "Head " + str(self.Head) +  "\nElbowLeft " + str(self.ElbowLeft ) + "\nElbowRight " + str(self.ElbowRight ) + "\nWristLeft " + str(self.WristLeft ) + "\nWristRight " + str(self.WristRight ) + "\nHandLeft " + str(self.HandLeft ) + "\nHandRight " + str(self.HandRight ) + "\nKneeLeft " + str(self.KneeLeft ) + "\nKneeRight " + str(self.KneeRight ) + "\nAnkleLeft " + str(self.AnkleLeft ) + "\nAnkleRight " + str(self.AnkleRight ) + "\nFootLeft " + str(self.FootLeft ) + "\nFootRight " + str(self.FootRight ) + "\nMidKneeRight " + str(self.MidKneeRight ) + "\nMidKneeLeft " + str(self.MidKneeLeft) 
        s += "-----------------\n"
        return s


def post_frame(frame):
    """Get skeleton events from the Kinect device and post them into the PyGame
    event queue."""
    try:
        pygame.event.post(
            pygame.event.Event(KINECTEVENT, skeleton_frame=frame)
        )
    except:
        # event queue full
        pass

    
def draw_skeleton_data(dispInfo, screen, pSkelton, index, positions, width = 4):
    start = pSkelton.SkeletonPositions[positions[0]]
       
    for position in itertools.islice(positions, 1, None):
        next = pSkelton.SkeletonPositions[position.value]
        
        curstart = skeleton_to_depth_image(start, dispInfo.current_w, dispInfo.current_h) 
        curend = skeleton_to_depth_image(next, dispInfo.current_w, dispInfo.current_h)

        pygame.draw.line(screen, SKELETON_COLORS[index], curstart, curend, width)
        
        start = next

def print_skeleton_data(skeleton_info):
    
    s = "---------------------------------"
    s+= "\nHEAD: "+str(skeleton_info.Head)
    s+= "\n...."
    s+= "\nLEft) ELBOW: "+str(skeleton_info.ElbowLeft)+" \tRIGht) ELBOW: "+str(skeleton_info.ElbowRight)
    s+= "\nLEft) WRIST: "+str(skeleton_info.WristLeft)+" \tRIGht) WRIST: "+str(skeleton_info.WristRight)
    s+= "\nLEft) HAND: "+str(skeleton_info.HandLeft)+" \tRIGht) HAND: "+str(skeleton_info.HandRight)
    s+= "\n...."
    s+= "\nLEft) KNEE: "+str(skeleton_info.KneeLeft)+" \tRIGht) KNEE: "+str(skeleton_info.KneeRight)
    s+= "\nLEft) ANKLE: "+str(skeleton_info.AnkleLeft)+" \tRIGht) ANKLE: "+str(skeleton_info.AnkleRight)
    s+= "\nLEft) FOOT: "+str(skeleton_info.FootLeft)+" \tRIGht) FOOT: "+str(skeleton_info.FootRight)
    s+= "\n---------------------------------\n"

    return s

class LoadingBox:
    def __init__(self):
        self.loading = 0
        self.text = "None"

    def draw(self, screen):
        
        if(self.loading >= 400):
            self.text = "Done"
            pygame.draw.rect(screen, pygame.color.THECOLORS["purple"], (700, 10, 20, 100))
        elif(self.loading < 400):
            self.text = "Loading"
            pygame.draw.rect(screen, pygame.color.THECOLORS["purple"], (700, 10, 20, self.loading))
            
        text = pygame.font.Font(None, 30).render(self.text, 1, pygame.color.THECOLORS["white"])
        textpos = text.get_rect()
        textpos.centerx = 700
        textpos.centery = 50
        screen.blit(text, textpos)


    def update_loading(self, loading):
        self.loading += loading

    def reset_loading(self):
        self.loading = 0
        
    

def draw_skeletons(dispInfo, screen, skeletons, loadingBox):
    # clean the screen
    c = OSC.OSCClient()
    c.connect(('127.0.0.1', 12000))   # localhost, port 57120
    text = "....."
    screen.fill(pygame.color.THECOLORS["black"])
    skeletonManager = SkeletonManager()
    for index, skeleton_info in enumerate(skeletons):
        # test if the current skeleton is tracked or not
        #print "---> ", index, "   ---> ",skeleton_info.eTrackingState
        if skeleton_info.eTrackingState == SkeletonTrackingState.TRACKED:
            #print index, "   TRACKED  "
            # draw the Head
            if(skeletonManager.num_skeletons() == 0):
                skeletonManager.create_skeleton(skeleton_info, index)
            else:
                            
                skeletonManager.update_skeletons(skeleton_info, index)
                
            HeadPos = skeleton_to_depth_image(skeleton_info.SkeletonPositions[JointId.Head], dispInfo.current_w, dispInfo.current_h)
            HipPos = skeleton_to_depth_image(skeleton_info.SkeletonPositions[JointId.HipCenter], dispInfo.current_w, dispInfo.current_h) 
            draw_skeleton_data(dispInfo, screen, skeleton_info, index, SPINE, 10)
            pygame.draw.circle(screen, SKELETON_COLORS[index], (int(HeadPos[0]), int(HeadPos[1])), 20, 0)
    
            # drawing the limbs
            draw_skeleton_data(dispInfo, screen, skeleton_info, index, LEFT_ARM)
            draw_skeleton_data(dispInfo, screen, skeleton_info, index, RIGHT_ARM)
            draw_skeleton_data(dispInfo, screen, skeleton_info, index, LEFT_LEG)
            draw_skeleton_data(dispInfo, screen, skeleton_info, index, RIGHT_LEG)

            #print skeletonManager.active_skeletons[index]
            kL = skeletonManager.active_skeletons[index].KneeLeft
            kR = skeletonManager.active_skeletons[index].KneeRight
            jog = skeletonManager.active_skeletons[index].detect_jogging()
            hipCenter = skeletonManager.active_skeletons[index].HipCenter
            
            '''text = pygame.font.Font(None, 30).render('kneeLeft '+str('%.3f' % kL.y)+"        kneeRight "+ str('%.3f' % kR.y) + "     jog "+str(jog)+",   hipCenter "+str('%.3f' % hipCenter.z), 1, pygame.color.THECOLORS["white"])
            textpos = text.get_rect()
            textpos.centerx = pygame.display.Info().current_w / 2
            textpos.centery = pygame.display.Info().current_h - 30
            screen.blit(text, textpos)'''

            if(jog):
                loadingBox.update_loading(2)
                '''if(loadingBox.loading <=100):
                    loadingBox.update_loading(4)
                elif(loadingBox.loading >400 and loadingBox.loading<=700):
                    loadingBox.update_loading(3)
                elif(loadingBox.loading >700 and loadingBox.loading<=900):
                    loadingBox.update_loading(2)
                elif(loadingBox.loading >900):
                    loadingBox.update_loading(1)'''
                if(loadingBox.loading<=400):
                    oscmsg = OSC.OSCMessage()
                    oscmsg.setAddress("/jog")
                    oscmsg.append(loadingBox.loading)
                    c.send(oscmsg)
            #print "ip: ", hipCenter.z
            if(hipCenter.z > 3):
                print "---> RESET LOADING"
                loadingBox.reset_loading()
                oscmsg = OSC.OSCMessage()
                oscmsg.setAddress("/jog")
                oscmsg.append(loadingBox.loading)
                c.send(oscmsg)

            #loadingBox.draw(screen)
        elif (index in skeletonManager.active_skeletons.keys()) and skeleton_info.eTrackingState == SkeletonTrackingState.TRACKED:
            print index, "   NOT TRACKED  "
            loadingBox.update_loading(0)
            oscmsg = OSC.OSCMessage()
            oscmsg.setAddress("/jog")
            oscmsg.append(loadingBox.loading)
            c.send(oscmsg)
            #print loadingBox.loading
           # pygame.draw.rect(pygame.display.Info(), pygame.color.THECOLORS["purple"], [700, 400, 20, 100])
            


WAIT_INTERVAL = 1.35
KINECTEVENT = pygame.USEREVENT            
display_w = 300
display_h = 300


def main():
    """Initialize and run the game."""
    pygame.init()
    keys_font = pygame.font.Font(None, 30)
    # Initialize PyGame
    screen = pygame.display.set_mode((display_w, display_h), 0, 16)
    pygame.display.set_caption('PyKinect Skeleton Example')
    screen.fill(pygame.color.THECOLORS["black"])
    loadingBox = LoadingBox()
    with nui.Runtime() as kinect:
        kinect.skeleton_engine.enabled = True
        kinect.skeleton_frame_ready += post_frame

        # Main game loop
        while True:
            event = pygame.event.wait()

            if event.type == pygame.QUIT:
                break
            elif event.type == KINECTEVENT:
                # apply joint filtering
                kinect._nui.NuiTransformSmooth(event.skeleton_frame, SMOOTH_PARAMS)
                draw_skeletons(pygame.display.Info(), screen, event.skeleton_frame.SkeletonData, loadingBox)
                pygame.display.update()
                pass

if __name__ == '__main__':
    main()
