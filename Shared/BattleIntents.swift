import AppIntents

/// 라이브 액티비티의 "스킬" 버튼. 라이브 액티비티 인텐트는 앱 본체 프로세스에서 실행된다.
struct SkillIntent: LiveActivityIntent {
    static var title: LocalizedStringResource = "스킬 사용"
    static var description = IntentDescription("현재 몬스터에게 강한 일격")

    init() {}

    func perform() async throws -> some IntentResult {
        await BattleController.shared.useSkill()
        return .result()
    }
}

/// 화면 갱신 버튼 (다음 몬스터로 넘어갔는지 다시 계산)
struct RefreshIntent: LiveActivityIntent {
    static var title: LocalizedStringResource = "전투 갱신"

    init() {}

    func perform() async throws -> some IntentResult {
        await BattleController.shared.reload()
        await BattleController.shared.pushUpdate(force: true)
        return .result()
    }
}
