import React from 'react';
import DiscInfo from './DiscInfo';
import renderer from 'react-test-renderer';

it('DiscInfo renders correctly', () => {
    const tree = renderer.create(
        <DiscInfo />
    ).toJSON();
    expect(tree).toMatchSnapshot();
});
