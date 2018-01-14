import React from 'react';
import Header from './Header';
import renderer from 'react-test-renderer';

it('Header renders correctly', () => {
    const tree = renderer.create(
        <Header />
    ).toJSON();
    expect(tree).toMatchSnapshot();
});
