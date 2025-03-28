void main() {
    float depth = length(pos - cameraPosition);
    FragColor = vec4(depth, depth, depth, 1.0f);
}
