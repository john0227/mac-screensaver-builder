#import "myscreensaverView.h"

@implementation myscreensaverView

- (instancetype)initWithFrame:(NSRect)frame isPreview:(BOOL)isPreview {
    self = [super initWithFrame:frame isPreview:isPreview];
    if (self) {
        self.wantsLayer = YES; // Enable layer backing for the view
        self.previewImage = [NSImage imageNamed:@"preview.png"];
    }
    return self;
}

- (void)startAnimation {
    [super startAnimation];

    // Video guaranteed to exist as either mp4, mov, or m4v
    NSURL *mp4URL = [[NSBundle bundleForClass:[self class]] URLForResource:@"video" withExtension:@"mp4"];
    NSURL *movURL = [[NSBundle bundleForClass:[self class]] URLForResource:@"video" withExtension:@"mov"];
    NSURL *m4vURL = [[NSBundle bundleForClass:[self class]] URLForResource:@"video" withExtension:@"m4v"];

    NSURL *videoURL;
    if ([[NSFileManager defaultManager] fileExistsAtPath:[mp4URL path]]) {
        videoURL = mp4URL;
    } else if ([[NSFileManager defaultManager] fileExistsAtPath:[movURL path]]) {
        videoURL = movURL;
    } else {
        videoURL = m4vURL;
    }

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

- (void)videoDidFinishPlaying:(NSNotification *)notification {
    [self.player seekToTime:kCMTimeZero];
    [self.player play];
}

- (void)stopAnimation {
    [super stopAnimation];
    [self.player pause];
    [[NSNotificationCenter defaultCenter] removeObserver:self];
}

- (void)drawRect:(NSRect)dirtyRect {
    [super drawRect:dirtyRect];

    // Check if the image is loaded
    if (self.previewImage) {
        // Calculate the image rect to center it
        NSRect imageRect;
        NSSize imageSize = [self.previewImage size];
        imageRect.size = imageSize;
        imageRect.origin.x = (NSWidth(self.bounds) - imageSize.width) / 2;
        imageRect.origin.y = (NSHeight(self.bounds) - imageSize.height) / 2;

        // Draw the image
        [self.previewImage drawInRect:imageRect];
    }
}

@end
