import { Box, Text } from "ink"
import TextInput from "ink-text-input"

interface InputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: (value: string) => void
  placeholder?: string
  disabled?: boolean
}

export function Input({ value, onChange, onSubmit, placeholder, disabled }: InputProps) {
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
