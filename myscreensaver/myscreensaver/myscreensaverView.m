#import "myscreensaverView.h"

@implementation myscreensaverView

- (instancetype)initWithFrame:(NSRect)frame isPreview:(BOOL)isPreview {
    self = [super initWithFrame:frame isPreview:isPreview];
    if (self) {
        self.wantsLayer = YES; // Enable layer backing for the view
    }
    return self;
}

- (void)startAnimation {
    [super startAnimation];

    NSURL *videoURL = [[NSBundle bundleForClass:[self class]] URLForResource:@"video" withExtension:@"mp4"];
    self.player = [AVPlayer playerWithURL:videoURL];

    self.playerLayer = [AVPlayerLayer playerLayerWithPlayer:self.player];
    self.playerLayer.frame = self.bounds;
    self.playerLayer.videoGravity = AVLayerVideoGravityResizeAspectFill;
    [self.layer addSublayer:self.playerLayer];

    [[NSNotificationCenter defaultCenter] addObserver:self
                                             selector:@selector(videoDidFinishPlaying:)
                                                 name:AVPlayerItemDidPlayToEndTimeNotification
                                               object:self.player.currentItem];

    [self.player play];
}

- (void)videoDidFinishPlaying:(NSNotification *)notification {
    [self.player seekToTime:kCMTimeZero];
    [self.player play];
}

- (void)stopAnimation {
    [super stopAnimation];
    [self.player pause];
    [[NSNotificationCenter defaultCenter] removeObserver:self];
}

@end
