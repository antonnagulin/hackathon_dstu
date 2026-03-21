package rating

func DetectLevel(score float64, thresholds Thresholds) string {
	switch {
	case score >= thresholds.BlackFrom:
		return "Black"
	case score >= thresholds.GoldFrom:
		return "Gold"
	default:
		return "Silver"
	}
}

func BuildNextLevel(score float64, currentLevel string, thresholds Thresholds) NextLevel {
	switch currentLevel {
	case "Silver":
		next := "Gold"
		missing := round2(max(0, thresholds.GoldFrom-score))
		return NextLevel{
			CurrentLevel: currentLevel,
			NextLevel:    &next,
			MissingScore: &missing,
		}
	case "Gold":
		next := "Black"
		missing := round2(max(0, thresholds.BlackFrom-score))
		return NextLevel{
			CurrentLevel: currentLevel,
			NextLevel:    &next,
			MissingScore: &missing,
		}
	default:
		return NextLevel{
			CurrentLevel: currentLevel,
			NextLevel:    nil,
			MissingScore: nil,
		}
	}
}
