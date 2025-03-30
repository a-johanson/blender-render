void main() {
    gl_Position = viewProjectionMatrix * vec4(position, 1.0f);
}
