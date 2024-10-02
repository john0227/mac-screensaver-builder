#import <ScreenSaver/ScreenSaver.h>
#import <AVKit/AVKit.h>
#import <AVFoundation/AVFoundation.h>

@interface screensaver_builderView : ScreenSaverView

@property (nonatomic, strong) AVPlayer *player;
@property (nonatomic, strong) AVPlayerLayer *playerLayer;
@property (nonatomic, strong) NSImage *firstFrameImage;

@end
