void main() {
    pos = position;
    norm = normal;
    gl_Position = projectionMatrix * vec4(position, 1.0f);
}
