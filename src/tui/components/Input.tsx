import { Box, Text } from "ink"
import Spinner from "ink-spinner"
import TextInput from "ink-text-input"

interface InputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: (value: string) => void
  placeholder?: string
  disabled?: boolean
  showSpinner?: boolean
}

export function Input({ value, onChange, onSubmit, placeholder, disabled, showSpinner }: InputProps) {
  if (showSpinner) {
    return (
      <Box>
        <Text color="yellow"><Spinner type="dots" /></Text>
        <Text dimColor> {placeholder}</Text>
      </Box>
    )
  }

  return (
    <Box>
      <Text color="green" bold>{">"} </Text>
      {disabled ? (
        <Text dimColor>{placeholder}</Text>
      ) : (
        <TextInput
          value={value}
          onChange={onChange}
          onSubmit={onSubmit}
          placeholder={placeholder}
        />
      )}
    </Box>
  )
}
