#import "screensaver_builderView.h"

@implementation screensaver_builderView

- (instancetype)initWithFrame:(NSRect)frame isPreview:(BOOL)isPreview {
    self = [super initWithFrame:frame isPreview:isPreview];
    if (self) {
        self.wantsLayer = YES; // Enable layer backing for the view
    }
    return self;
}

- (void)startAnimation {
    [super startAnimation];

    NSURL *videoURL = [[NSBundle bundleForClass:[self class]] URLForResource:@"{{video_path}}" withExtension:nil];
    AVAsset *asset = [AVAsset assetWithURL:videoURL];
    AVAssetImageGenerator *imageGenerator = [AVAssetImageGenerator assetImageGeneratorWithAsset:asset];

    // Generate the first frame
    CMTime time = CMTimeMake(0, 1); // 0 seconds
    [imageGenerator generateCGImagesAsynchronouslyForTimes:@[[NSValue valueWithCMTime:time]]
                                          completionHandler:^(CMTime requestedTime, CGImageRef image, CMTime actualTime, AVAssetImageGeneratorResult result, NSError *error) {
        if (result == AVAssetImageGeneratorSucceeded && image) {
            self.firstFrameImage = [[NSImage alloc] initWithCGImage:image size:NSZeroSize];
            [self setNeedsDisplay:YES]; // Request a redraw
        }
    }];
    
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

    if (self.firstFrameImage) {
        [self.firstFrameImage drawInRect:self.bounds];
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
