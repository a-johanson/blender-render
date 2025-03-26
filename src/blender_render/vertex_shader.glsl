void main() {
    pos = position;
    norm = normal;
    gl_Position = viewProjectionMatrix * vec4(position, 1.0f);
}
