import ActivityKit
import Foundation

enum SpriteRenderMode: String, Codable, Hashable, CaseIterable {
    case color     // 컬러 글꼴(sbix) 한 겹
    case layered   // 한 색 글꼴 여러 겹
    case still     // 그림 파일 (움직이지 않음, 비교용)

    var label: String {
        switch self {
        case .color: "컬러 글꼴"
        case .layered: "겹친 글꼴"
        case .still: "정지 그림"
        }
    }
}

struct BattleAttributes: ActivityAttributes {
    struct ContentState: Codable, Hashable {
        var monster: MonsterKind
        var monsterIndex: Int
        var kills: Int
        var gold: Int
        var hpBarStart: Date
        var deathDate: Date
        /// 애니메이션 기준 시각 (구간 시작). 이 시각부터 흐른 초의 일의 자리가 프레임 번호.
        var animStart: Date
        var renderMode: SpriteRenderMode
        /// 스킬을 쓴 시각 (3초 동안 폭발 이펙트)
        var skillAt: Date?
    }
}

extension BattleAttributes.ContentState {
    init(status st: BattleStatus, segment: BattleSegment, mode: SpriteRenderMode, skillAt: Date?) {
        self.init(monster: st.kind, monsterIndex: st.monsterIndex, kills: st.kills, gold: st.gold,
                  hpBarStart: st.hpBarStart, deathDate: st.deathDate,
                  animStart: segment.start, renderMode: mode, skillAt: skillAt)
    }
}
