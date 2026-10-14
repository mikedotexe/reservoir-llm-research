use crate::{
    files::{self, AppError},
    resources,
};
use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Clone, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Example {
    pub id: String,
    pub title: String,
    pub file: String,
    pub format: String,
    pub provenance: String,
    pub group: String,
    pub order: u64,
    #[serde(rename(deserialize = "lessonID", serialize = "lessonId"))]
    pub lesson_id: Option<String>,
}

#[derive(Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Lesson {
    pub stage: u8,
    pub title: String,
    pub question: String,
    pub suggested_action: String,
    pub expected: String,
    pub model_expected: String,
    pub limitation: String,
    pub focus: String,
    pub checkpoints: Vec<u64>,
    pub scripted_file: String,
    pub model_file: Option<String>,
}

#[derive(Deserialize)]
struct AuthoredCatalog {
    format: String,
    lessons: Vec<Lesson>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct GuideLesson {
    #[serde(flatten)]
    pub lesson: Lesson,
    pub scripted_example: Example,
    pub model_example: Option<Example>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct GuideCatalog {
    pub format: String,
    pub lessons: Vec<GuideLesson>,
    pub comparisons: Vec<Example>,
    pub lessons_sha256: String,
    pub examples_sha256: String,
}

fn invalid(message: impl Into<String>) -> AppError {
    AppError::new("guided-catalog", "invalid-catalog", message)
}
fn plain_json(name: &str) -> bool {
    !name.contains(['/', '\\']) && !name.contains("..") && name.ends_with(".json") && name.len() > 5
}

pub fn catalog(root: &Path) -> Result<GuideCatalog, AppError> {
    // Both files are checked against identities compiled into this executable.
    let lessons = resources::catalog_bytes(root, "guided-lessons.json")?;
    let examples = resources::catalog_bytes(root, "examples-index.json")?;
    parse(&lessons, &examples)
}

fn parse(lessons_bytes: &[u8], examples_bytes: &[u8]) -> Result<GuideCatalog, AppError> {
    let authored: AuthoredCatalog =
        serde_json::from_slice(lessons_bytes).map_err(|e| invalid(e.to_string()))?;
    let examples: Vec<Example> =
        serde_json::from_slice(examples_bytes).map_err(|e| invalid(e.to_string()))?;
    if authored.format != "reservoir-guided-lessons-v1"
        || authored.lessons.iter().map(|l| l.stage).collect::<Vec<_>>()
            != (1..=8).collect::<Vec<_>>()
    {
        return Err(invalid(
            "The guide must contain authored lessons A–H in order.",
        ));
    }
    let mut ids = std::collections::HashSet::new();
    if examples.iter().any(|e| {
        !ids.insert(e.id.as_str())
            || !plain_json(&e.file)
            || e.id.is_empty()
            || e.title.is_empty()
            || e.provenance.is_empty()
    }) {
        return Err(invalid(
            "Example metadata has an invalid filename, identity or provenance.",
        ));
    }
    let mut lessons = Vec::with_capacity(8);
    let focuses = [
        "inputState",
        "recurrence",
        "sensory",
        "journal",
        "feedback",
        "memory",
        "choice",
        "regulation",
    ];
    for lesson in authored.lessons {
        if [
            &lesson.title,
            &lesson.question,
            &lesson.suggested_action,
            &lesson.expected,
            &lesson.model_expected,
            &lesson.limitation,
        ]
        .iter()
        .any(|s| s.is_empty())
            || lesson.focus != focuses[usize::from(lesson.stage) - 1]
            || lesson.checkpoints.is_empty()
            || lesson.checkpoints.iter().any(|s| !(1..=600).contains(s))
            || lesson.checkpoints.windows(2).any(|s| s[0] >= s[1])
            || !plain_json(&lesson.scripted_file)
            || lesson.model_file.as_deref().is_some_and(|f| !plain_json(f))
            || (lesson.stage >= 4 && lesson.model_file.is_none())
        {
            return Err(invalid(format!(
                "Lesson {} has invalid authored fields or checkpoint boundaries.",
                lesson.stage
            )));
        }
        let letter = char::from(b'A' + lesson.stage - 1).to_string();
        let resolve = |file: &str, group: &str| -> Result<Example, AppError> {
            let matching: Vec<_> = examples
                .iter()
                .filter(|e| {
                    e.file == file
                        && e.group == group
                        && e.lesson_id.as_deref() == Some(letter.as_str())
                })
                .collect();
            if matching.len() != 1 {
                return Err(invalid(format!(
                    "Lesson {letter} must have one explicit {group} source."
                )));
            }
            Ok(matching[0].clone())
        };
        let scripted_example = resolve(&lesson.scripted_file, "guided")?;
        let model_example = lesson
            .model_file
            .as_deref()
            .map(|f| resolve(f, "model"))
            .transpose()?;
        lessons.push(GuideLesson {
            lesson,
            scripted_example,
            model_example,
        });
    }
    let mut comparisons: Vec<_> = examples
        .into_iter()
        .filter(|e| e.group == "comparison")
        .collect();
    comparisons.sort_by_key(|e| e.order);
    Ok(GuideCatalog {
        format: authored.format,
        lessons,
        comparisons,
        lessons_sha256: files::digest(lessons_bytes),
        examples_sha256: files::digest(examples_bytes),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    fn source() -> (Vec<u8>, Vec<u8>) {
        let root =
            Path::new(env!("CARGO_MANIFEST_DIR")).join("../../../essentials/examples/portable");
        (
            std::fs::read(root.join("guided-lessons.json")).unwrap(),
            std::fs::read(root.join("examples-index.json")).unwrap(),
        )
    }
    #[test]
    fn catalog_rejects_changed_packaged_authorship() {
        let root = tempfile::tempdir().unwrap();
        let (lessons, examples) = source();
        std::fs::write(root.path().join("guided-lessons.json"), &lessons).unwrap();
        std::fs::write(root.path().join("examples-index.json"), &examples).unwrap();
        assert!(catalog(root.path()).is_ok());
        std::fs::write(root.path().join("guided-lessons.json"), b"{}").unwrap();
        assert!(catalog(root.path()).is_err());
    }
    #[test]
    fn authored_journey_and_recorded_model_sources_are_retained() {
        let (lessons, examples) = source();
        let result = parse(&lessons, &examples).unwrap();
        assert_eq!(result.lessons.len(), 8);
        assert!(result.lessons[..3]
            .iter()
            .all(|l| l.model_example.is_none()));
        assert_eq!(result.lessons[4].lesson.checkpoints, [30, 31, 60, 61]);
        assert_eq!(
            result.lessons[6].model_example.as_ref().unwrap().id,
            "example-model-7"
        );
        assert_eq!(
            result.lessons[6].lesson.model_expected,
            "Inspect the actual recorded choices. Writing at every opportunity is a valid outcome."
        );
        assert!(result
            .comparisons
            .iter()
            .any(|e| e.id == "regulation-controller"));
    }
    #[test]
    fn rejects_nonordered_checkpoints_and_path_escape() {
        let (lessons, examples) = source();
        let mut value: serde_json::Value = serde_json::from_slice(&lessons).unwrap();
        value["lessons"][0]["checkpoints"] = serde_json::json!([12, 1]);
        assert!(parse(&serde_json::to_vec(&value).unwrap(), &examples).is_err());
        value["lessons"][0]["checkpoints"] = serde_json::json!([1, 12]);
        value["lessons"][0]["scriptedFile"] = serde_json::json!("../example-component-1.json");
        assert!(parse(&serde_json::to_vec(&value).unwrap(), &examples).is_err());
    }
    #[test]
    fn rejects_missing_or_mislabeled_model_source() {
        let (lessons, examples) = source();
        let mut values: Vec<serde_json::Value> = serde_json::from_slice(&examples).unwrap();
        values.retain(|v| v["id"] != "example-model-4");
        assert!(parse(&lessons, &serde_json::to_vec(&values).unwrap()).is_err());
    }
}
