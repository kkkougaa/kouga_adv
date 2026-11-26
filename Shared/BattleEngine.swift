import Foundation

// MARK: - 몬스터

enum MonsterKind: String, Codable, Hashable, CaseIterable {
    case slime, goblin, bat, dragon, skull, skeleton, mushroom, eyeball, mummy, cactus, robot

    var displayName: String {
        switch self {
        case .slime: "슬라임"
        case .goblin: "고블린"
        case .bat: "박쥐"
        case .dragon: "드래곤"
        case .skull: "해골"
        case .skeleton: "스켈레톤"
        case .mushroom: "버섯"
        case .eyeball: "눈알"
        case .mummy: "미라"
        case .cactus: "선인장"
        case .robot: "로봇"
        }
    }

    var anim: SpriteAnim {
        switch self {
        case .slime: SpriteCatalog.slimeBattle
        case .goblin: SpriteCatalog.goblinBattle
        case .bat: SpriteCatalog.batBattle
        case .dragon: SpriteCatalog.dragonBattle
        case .skull: SpriteCatalog.skullBattle
        case .skeleton: SpriteCatalog.skeletonBattle
        case .mushroom: SpriteCatalog.mushroomBattle
        case .eyeball: SpriteCatalog.eyeballBattle
        case .mummy: SpriteCatalog.mummyBattle
        case .cactus: SpriteCatalog.cactusBattle
        case .robot: SpriteCatalog.robotBattle
        }
    }
}

enum MonsterTable {
    static let regular: [MonsterKind] = [.slime, .goblin, .bat, .skull, .skeleton,
                                         .mushroom, .eyeball, .mummy, .cactus, .robot]

    /// 10마리마다 보스(드래곤), 나머지는 순서대로 돌아가며 등장
    static func kind(at index: Int) -> MonsterKind {
        if (index + 1) % 10 == 0 { return .dragon }
        return regular[(index - index / 10) % regular.count]
    }

    static func maxHP(at index: Int) -> Int {
        let base = 12.0 * pow(1.08, Double(index))
        return Int(base) * (kind(at: index) == .dragon ? 5 : 1)
    }

    static func gold(at index: Int) -> Int {
        let base = 3 + index / 2
        return kind(at: index) == .dragon ? base * 10 : base
    }
}

// MARK: - 능력치

struct HeroStats: Codable, Hashable {
    var attackLevel: Int = 1

    var attack: Int { 3 + (attackLevel - 1) * 2 }
    var upgradeCost: Int { Int(10 * pow(Double(attackLevel), 1.5)) }

    /// 글꼴 애니메이션이 2초 주기(짝수 초 = 베기)라서 공격 간격도 2초에 맞춤
    static let attackInterval: TimeInterval = 2
    static let skillMultiplier = 5
}

// MARK: - 전투 구간
// 전투는 "구간" 단위로 결정론적으로 계산한다.
// 구간 = (시작 시각, 시작 몬스터 번호, 그 몬스터의 남은 체력, 그때까지 처치 수/골드, 공격력)
// 스킬이나 강화로 상황이 바뀌면 그 시점에서 새 구간을 연다.

struct BattleSegment: Codable, Hashable {
    var start: Date
    var monsterIndex: Int
    var monsterHP: Int
    var kills: Int
    var gold: Int
    var attack: Int
}

struct BattleStatus: Hashable {
    var monsterIndex: Int
    var kind: MonsterKind
    var hp: Int
    var maxHP: Int
    var kills: Int
    var gold: Int
    /// 체력바용: 이 몬스터를 처음부터 때렸다면 체력이 꽉 차 있었을 가상 시각
    var hpBarStart: Date
    /// 지금 몬스터가 쓰러지는 시각
    var deathDate: Date
}

enum BattleEngine {
    static func newBattle(at now: Date, stats: HeroStats) -> BattleSegment {
        BattleSegment(start: now, monsterIndex: 0, monsterHP: MonsterTable.maxHP(at: 0),
                      kills: 0, gold: 0, attack: stats.attack)
    }

    static func status(_ s: BattleSegment, at now: Date) -> BattleStatus {
        let interval = HeroStats.attackInterval
        let atk = max(1, s.attack)
        var t = max(0, now.timeIntervalSince(s.start))
        var fightStart = s.start
        var idx = s.monsterIndex
        var hp = s.monsterHP
        var kills = s.kills
        var gold = s.gold

        for _ in 0..<200_000 {
            let hits = (hp + atk - 1) / atk
            let duration = Double(hits) * interval
            if t >= duration {
                t -= duration
                fightStart += duration
                kills += 1
                gold += MonsterTable.gold(at: idx)
                idx += 1
                hp = MonsterTable.maxHP(at: idx)
            } else {
                let death = fightStart.addingTimeInterval(duration)
                let done = Int(t / interval)
                hp -= done * atk
                let maxHP = MonsterTable.maxHP(at: idx)
                let full = Double((maxHP + atk - 1) / atk) * interval
                return BattleStatus(monsterIndex: idx, kind: MonsterTable.kind(at: idx),
                                    hp: hp, maxHP: maxHP, kills: kills, gold: gold,
                                    hpBarStart: death.addingTimeInterval(-full), deathDate: death)
            }
        }
        // 여기까지 올 일은 거의 없음
        let maxHP = MonsterTable.maxHP(at: idx)
        return BattleStatus(monsterIndex: idx, kind: MonsterTable.kind(at: idx), hp: hp, maxHP: maxHP,
                            kills: kills, gold: gold, hpBarStart: now, deathDate: now.addingTimeInterval(interval))
    }

    /// 지금 시점에서 새 구간을 연다 (공격력 변경 등)
    static func rebase(_ s: BattleSegment, at now: Date, attack: Int) -> BattleSegment {
        let st = status(s, at: now)
        return BattleSegment(start: now, monsterIndex: st.monsterIndex, monsterHP: st.hp,
                             kills: st.kills, gold: st.gold, attack: attack)
    }

    static func useSkill(_ s: BattleSegment, at now: Date) -> BattleSegment {
        var seg = rebase(s, at: now, attack: s.attack)
        seg.monsterHP -= s.attack * HeroStats.skillMultiplier
        if seg.monsterHP <= 0 {
            seg.kills += 1
            seg.gold += MonsterTable.gold(at: seg.monsterIndex)
            seg.monsterIndex += 1
            seg.monsterHP = MonsterTable.maxHP(at: seg.monsterIndex)
        }
        return seg
    }
}
