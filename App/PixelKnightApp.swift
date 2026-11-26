import SwiftUI

@main
struct PixelKnightApp: App {
    @StateObject private var controller = BattleController.shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(controller)
                .preferredColorScheme(.dark)
        }
    }
}
