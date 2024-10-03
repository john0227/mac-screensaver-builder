#import <ScreenSaver/ScreenSaver.h>
#import <AVKit/AVKit.h>

@interface myscreensaverView : ScreenSaverView

@property (strong) AVPlayer *player;
@property (strong) AVPlayerLayer *playerLayer;
@property (strong) NSImage *previewImage;

@end
