from typing import Optional


class AssetDefinitionError(Exception):
    def __init__(
            self,
            *,
            error: str,
            explanation: Optional[str] = None,
            fix: Optional[str] = None,
            description: Optional[str] = None,
            docs_ref: Optional[str] = None,
    ):
        self.error = error
        self.explanation = explanation
        self.fix = fix
        self.description = description
        self.docs_ref = docs_ref

        message = [error]
        if explanation:
            message.append(explanation)
        if fix:
            message.append(fix)
        if docs_ref:
            message.append(f"For more information, please see: {self.docs_ref}.")

        super().__init__(" ".join(message))
