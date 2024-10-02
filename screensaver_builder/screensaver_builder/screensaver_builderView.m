#import "screensaver_builderView.h"

@implementation screensaver_builderView

- (instancetype)initWithFrame:(NSRect)frame isPreview:(BOOL)isPreview {
    self = [super initWithFrame:frame isPreview:isPreview];
    if (self) {
        self.wantsLayer = YES; // Enable layer backing for the view
        NSURL *imageURL = [[NSBundle bundleForClass:[self class]] URLForResource:@"asset/preview" withExtension:nil];
        self.previewImage = [[NSImage alloc] initWithContentsOfURL:imageURL];
    }
    return self;
}

- (void)startAnimation {
    [super startAnimation];

    NSURL *videoURL = [[NSBundle bundleForClass:[self class]] URLForResource:@"asset/video" withExtension:nil];
    AVAsset *asset = [AVAsset assetWithURL:videoURL];
    AVAssetImageGenerator *imageGenerator = [AVAssetImageGenerator assetImageGeneratorWithAsset:asset];
    
    self.player = [AVPlayer playerWithURL:videoURL];
    self.player.volume = 0.0;

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

- (void)drawRect:(NSRect)dirtyRect {
    [super drawRect:dirtyRect];

    if (self.previewImage) {
        [self.previewImage drawInRect:self.bounds];
    }
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
