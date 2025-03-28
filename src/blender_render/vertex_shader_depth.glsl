void main() {
    pos = position;
    gl_Position = viewProjectionMatrix * vec4(position, 1.0f);
}
