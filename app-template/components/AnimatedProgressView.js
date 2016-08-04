
var React = require('react-native');
var {
  StyleSheet,
  View,
  Platform,
  ProgressViewIOS,
  ProgressBarAndroid,
} = React;


var ProgressView = React.createClass({
  propTypes: {
    ...View.propTypes,
    barColor: React.PropTypes.string,
    progress: React.PropTypes.number,
  },
  render: function() {
    if (Platform.OS == 'android') {
      return (
        <ProgressBarAndroid
          style={this.props.style}
          styleAttr='Horizontal'
          indeterminate={false}
          color={this.props.barColor}
          progress={this.props.progress}/>
        );
    } else {
      return (
        <ProgressViewIOS
          style={this.props.style}
          progressTintColor={this.props.barColor}
          progress={this.props.progress}/>
        );
    }
  },
});

var AnimatedProgressView = React.createClass({
  getInitialState: function() {
    return {progress: 0};
  },

  componentDidMount: function() {
    this.updateProgress();
  },

  updateProgress() {
    var progress = this.state.progress + 0.01;
    this.setState({progress: progress});
    requestAnimationFrame(() => this.updateProgress());
  },

  getProgress: function(offset) {
    var progress = this.state.progress + offset;
    return Math.sin(progress % Math.PI) % 1;
  },

  render: function() {
    return (
      <View style={styles.container}>
        <ProgressView
          style={styles.progress}
          barColor='purple'
          progress={this.getProgress(0.2)}
        />
        <ProgressView
          style={styles.progress}
          barColor='red'
          progress={this.getProgress(0.4)}
        />
        <ProgressView
          style={styles.progress}
          barColor='orange'
          progress={this.getProgress(0.6)}
        />
        <ProgressView
          style={styles.progress}
          barColor='yellow'
          progress={this.getProgress(0.8)}
        />
      </View>
    );
  }
});

var styles = StyleSheet.create({
  container: {
    backgroundColor: 'white',
    marginTop: 10,
    marginBottom: 10
  },
  progress: {
    margin: 10
  }
});

module.exports = AnimatedProgressView;
