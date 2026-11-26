import Foundation

struct GameState: Codable, Hashable {
    var bankedGold: Int = 0
    var stats = HeroStats()
    var segment: BattleSegment?
    var renderMode: SpriteRenderMode = .color
    var lastSkillAt: Date?
}

/// 앱 그룹 저장소. 페더 인증서가 앱 그룹을 지원하지 않으면 일반 저장소로 동작한다.
/// (라이브 액티비티 버튼의 앱 인텐트는 앱 본체 프로세스에서 실행되므로 일반 저장소여도 문제 없음)
enum GameStore {
    static let appGroupID = "group.com.pixelknight.app"
    private static let key = "gameState.v1"

    static var defaults: UserDefaults {
        UserDefaults(suiteName: appGroupID) ?? .standard
    }

    static func load() -> GameState {
        guard let data = defaults.data(forKey: key),
              let s = try? JSONDecoder().decode(GameState.self, from: data) else { return GameState() }
        return s
    }

    static func save(_ s: GameState) {
        if let data = try? JSONEncoder().encode(s) { defaults.set(data, forKey: key) }
    }
}
